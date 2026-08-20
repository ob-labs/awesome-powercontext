from __future__ import annotations

import asyncio
import json
from collections.abc import Coroutine, Mapping
from concurrent.futures import Future
from hashlib import sha256
from threading import Event, Thread
from typing import Any

from powercontext.builtin.artifacts.memory import (
    MemoryCandidateRequest,
    MemoryEntryInput,
)
from powercontext.builtin.persistence.oceanbase import OceanBaseConfig
from powercontext.builtin.persistence.sqlite import SQLiteConfig
from powercontext.builtin.runtime import (
    BuiltinConfig,
    CaptureSource,
    HandoffReportConfig,
    RetireMemoryEntryRequest,
    ReviseMemoryEntryRequest,
    SearchMemoryRequest,
    open_builtin_runtime,
)
from powercontext.builtin.sources import ContentSource
from pydantic import JsonValue, SecretStr

ENTRY_SCHEMA = "awesome-powercontext.smart-ev-memory.v1"
SOURCE_SCHEMA = "awesome-powercontext.smart-ev-source.v1"
DEFAULT_OPERATION_TIMEOUT_SECONDS = 30.0
DEFAULT_SEARCH_CANDIDATE_LIMIT = 100


class PowerContextRuntimeError(RuntimeError):
    pass


class _CockpitMemoryPipeline:
    """Turn captured cockpit Sources into cited PowerContext Memory entries."""

    async def extract(
        self,
        request: MemoryCandidateRequest,
        /,
    ) -> tuple[MemoryEntryInput, ...]:
        entries: list[MemoryEntryInput] = []
        for source in request.sources:
            if not isinstance(source, ContentSource):
                continue
            source_metadata = source.metadata
            metadata = source_metadata.get("memory_metadata")
            if not isinstance(metadata, dict):
                continue
            user_id = source_metadata.get("user_id")
            if not isinstance(user_id, str) or not user_id:
                continue
            entries.append(
                MemoryEntryInput(
                    kind=str(metadata.get("memory_kind") or "fact"),
                    text=_encode_entry(source.content, metadata, user_id),
                    sources=(source,),
                )
            )
        return tuple(entries)


class EmbeddedPowerContextMemory:
    """Synchronous facade over one lifecycle-owned asynchronous Builtin Runtime."""

    def __init__(
        self,
        *,
        config: BuiltinConfig,
        scope_id: str,
        operation_timeout_seconds: float = DEFAULT_OPERATION_TIMEOUT_SECONDS,
    ) -> None:
        self._config = config
        self._scope_id = scope_id
        self._operation_timeout_seconds = operation_timeout_seconds
        self._ready = Event()
        self._thread = Thread(
            target=self._thread_main,
            name="powercontext-smart-ev-runtime",
            daemon=True,
        )
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop: asyncio.Event | None = None
        self._runtime: Any | None = None
        self._ingestion_lock: asyncio.Lock | None = None
        self._startup_error: BaseException | None = None
        self._closed = False
        self._thread.start()
        if not self._ready.wait(timeout=operation_timeout_seconds):
            self.close()
            raise PowerContextRuntimeError("PowerContext Runtime startup timed out")
        if self._startup_error is not None:
            raise PowerContextRuntimeError(
                f"PowerContext Runtime startup failed: {self._startup_error}"
            ) from self._startup_error

    def add(
        self,
        content: str | list[dict[str, str]],
        *,
        user_id: str,
        metadata: dict,
        infer: bool = False,
    ) -> dict:
        normalized_content = _message_content(content)
        return self._call(
            self._capture_and_remember(
                content=normalized_content,
                user_id=user_id,
                metadata=metadata,
                infer=infer,
            )
        )

    def search(
        self,
        *,
        query: str,
        user_id: str | None = None,
        filters: dict | None = None,
        limit: int = 10,
    ) -> dict:
        return self._call(
            self._search(
                query=query,
                user_id=user_id,
                filters=filters,
                limit=limit,
            )
        )

    def get_all(
        self,
        *,
        filters: dict | None = None,
        user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        return self._call(
            self._get_all(
                filters=filters,
                user_id=user_id,
                limit=limit,
                offset=offset,
            )
        )

    def update(self, *, memory_id: str, content: str, metadata: dict) -> dict:
        return self._call(
            self._update(memory_id=memory_id, content=content, metadata=metadata)
        )

    def delete(self, *, memory_id: str) -> bool:
        return self._call(self._delete(memory_id))

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        loop = self._loop
        stop = self._stop
        if loop is not None and stop is not None and loop.is_running():
            loop.call_soon_threadsafe(stop.set)
        if self._thread.is_alive():
            self._thread.join(timeout=self._operation_timeout_seconds)

    async def _capture_and_remember(
        self,
        *,
        content: str,
        user_id: str,
        metadata: dict,
        infer: bool,
    ) -> dict:
        runtime = self._require_runtime()
        lock = self._require_ingestion_lock()
        async with lock:
            memory = runtime.memory.for_scope(self._scope_id)
            before = await memory.list()
            before_entries = {entry.entry.entry_id: entry for entry in before.entries}
            source_id = _source_id(content, metadata, user_id)
            await runtime.sources.for_scope(self._scope_id).capture(
                CaptureSource(
                    source_id=source_id,
                    content=content,
                    metadata={
                        "schema": SOURCE_SCHEMA,
                        "user_id": user_id,
                        "memory_metadata": _json_mapping(metadata),
                        "infer_requested": infer,
                    },
                )
            )
            await memory.flush()
            after = await memory.list()
            changed = [
                entry
                for entry in after.entries
                if entry.entry.entry_id not in before_entries
                or before_entries[entry.entry.entry_id].entry.entry_version_id
                != entry.entry.entry_version_id
            ]
            idempotent_retry = not changed
            if idempotent_retry:
                expected_text = _encode_entry(content, metadata, user_id)
                changed = [
                    entry
                    for entry in after.entries
                    if entry.entry.text == expected_text
                ]
            return {
                "results": [
                    {
                        **_row_from_entry(entry),
                        "event": (
                            "UPDATE"
                            if not idempotent_retry
                            and entry.entry.entry_id in before_entries
                            else "ADD"
                        ),
                        "previous_memory": (
                            _row_from_entry(before_entries[entry.entry.entry_id])["memory"]
                            if not idempotent_retry
                            and entry.entry.entry_id in before_entries
                            else None
                        ),
                    }
                    for entry in changed
                ]
            }

    async def _search(
        self,
        *,
        query: str,
        user_id: str | None,
        filters: dict | None,
        limit: int,
    ) -> dict:
        memory = self._require_runtime().memory.for_scope(self._scope_id)
        candidate_limit = max(DEFAULT_SEARCH_CANDIDATE_LIMIT, limit * 10)
        page = await memory.search(
            SearchMemoryRequest(query=query, limit=candidate_limit, mode="fts")
        )
        rows = []
        for hit in page.hits:
            row = _row_from_hit(hit)
            if _row_matches(row, filters=filters, user_id=user_id):
                rows.append(row)
            if len(rows) == limit:
                break
        return {"results": rows}

    async def _get_all(
        self,
        *,
        filters: dict | None,
        user_id: str | None,
        limit: int,
        offset: int,
    ) -> dict:
        memory = self._require_runtime().memory.for_scope(self._scope_id)
        page = await memory.list()
        rows = []
        for entry in page.entries:
            row = _row_from_entry(entry)
            if _row_matches(row, filters=filters, user_id=user_id):
                rows.append(row)
        return {"results": rows[offset : offset + limit]}

    async def _update(self, *, memory_id: str, content: str, metadata: dict) -> dict:
        memory = self._require_runtime().memory.for_scope(self._scope_id)
        entry = await self._find_entry(memory_id)
        decoded = _decode_entry(entry.entry.text)
        user_id = str(decoded["user_id"])
        result = await memory.revise(
            ReviseMemoryEntryRequest(
                citation=entry.citation,
                kind=str(metadata.get("memory_kind") or entry.entry.kind),
                text=_encode_entry(content, metadata, user_id),
                reason="Smart EV cockpit lifecycle update",
            )
        )
        if result.entry is None:
            raise PowerContextRuntimeError("PowerContext did not return the revised entry")
        return {"success": True, **_row_from_entry(result.entry)}

    async def _delete(self, memory_id: str) -> bool:
        memory = self._require_runtime().memory.for_scope(self._scope_id)
        entry = await self._find_entry(memory_id)
        result = await memory.retire(
            RetireMemoryEntryRequest(
                citation=entry.citation,
                reason="Smart EV cockpit lifecycle retirement",
            )
        )
        return result.entry is not None and result.entry.state == "inactive"

    async def _find_entry(self, memory_id: str):
        page = await self._require_runtime().memory.for_scope(self._scope_id).list()
        for entry in page.entries:
            if entry.entry.entry_id == memory_id:
                return entry
        raise PowerContextRuntimeError(f"PowerContext Memory entry {memory_id} was not found")

    def _call(self, operation: Coroutine[Any, Any, Any]) -> Any:
        if self._closed:
            operation.close()
            raise PowerContextRuntimeError("PowerContext Runtime is closed")
        loop = self._loop
        if loop is None or not loop.is_running():
            operation.close()
            raise PowerContextRuntimeError("PowerContext Runtime is not running")
        future: Future[Any] = asyncio.run_coroutine_threadsafe(operation, loop)
        return future.result(timeout=self._operation_timeout_seconds)

    def _thread_main(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self._serve())
        except BaseException as exc:
            self._startup_error = exc
            self._ready.set()
        finally:
            loop.close()

    async def _serve(self) -> None:
        self._stop = asyncio.Event()
        try:
            async with open_builtin_runtime(
                self._config,
                candidate_pipeline=_CockpitMemoryPipeline(),
            ) as runtime:
                self._runtime = runtime
                self._ingestion_lock = asyncio.Lock()
                self._ready.set()
                await self._stop.wait()
        finally:
            self._runtime = None
            self._ingestion_lock = None

    def _require_runtime(self):
        if self._runtime is None:
            raise PowerContextRuntimeError("PowerContext Runtime is not available")
        return self._runtime

    def _require_ingestion_lock(self) -> asyncio.Lock:
        if self._ingestion_lock is None:
            raise PowerContextRuntimeError("PowerContext ingestion is not available")
        return self._ingestion_lock


def powercontext_config(database_url: str) -> BuiltinConfig:
    if database_url.startswith("sqlite+aiosqlite:"):
        database = SQLiteConfig(url=database_url)
    elif database_url.startswith("mysql+aoceanbase:"):
        database = OceanBaseConfig(url=SecretStr(database_url))
    else:
        raise ValueError(
            "POWERCONTEXT_DATABASE_URL must use sqlite+aiosqlite or mysql+aoceanbase"
        )
    return BuiltinConfig(
        database=database,
        handoff_report=HandoffReportConfig(enabled=False),
    )


def _encode_entry(content: str, metadata: Mapping[str, Any], user_id: str) -> str:
    return json.dumps(
        {
            "schema": ENTRY_SCHEMA,
            "content": content,
            "metadata": _json_mapping(metadata),
            "user_id": user_id,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _decode_entry(value: str) -> dict[str, Any]:
    try:
        decoded = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise PowerContextRuntimeError(
            "PowerContext Memory entry is not a cockpit envelope"
        ) from exc
    if not isinstance(decoded, dict) or decoded.get("schema") != ENTRY_SCHEMA:
        raise PowerContextRuntimeError("PowerContext Memory entry has an unsupported schema")
    if not isinstance(decoded.get("content"), str):
        raise PowerContextRuntimeError("PowerContext Memory entry content is invalid")
    if not isinstance(decoded.get("metadata"), dict):
        raise PowerContextRuntimeError("PowerContext Memory entry metadata is invalid")
    if not isinstance(decoded.get("user_id"), str):
        raise PowerContextRuntimeError("PowerContext Memory entry user_id is invalid")
    return decoded


def _row_from_entry(entry) -> dict[str, Any]:
    decoded = _decode_entry(entry.entry.text)
    return {
        "id": entry.entry.entry_id,
        "memory": decoded["content"],
        "metadata": decoded["metadata"],
        "user_id": decoded["user_id"],
        "created_at": decoded["metadata"].get("created_at"),
        "powercontext": {
            "memory_ref": entry.memory_ref.model_dump(mode="json"),
            "entry_version_id": entry.entry.entry_version_id,
            "state": entry.state,
            "source_refs": [
                source.model_dump(mode="json") for source in entry.entry.sources
            ],
        },
    }


def _row_from_hit(hit) -> dict[str, Any]:
    decoded = _decode_entry(hit.text)
    return {
        "id": hit.entry_id,
        "memory": decoded["content"],
        "metadata": decoded["metadata"],
        "user_id": decoded["user_id"],
        "created_at": decoded["metadata"].get("created_at"),
        "score": hit.score,
        "powercontext": {
            "memory_ref": hit.memory_ref.model_dump(mode="json"),
            "entry_version_id": hit.entry_version_id,
            "matched_by": list(hit.matched_by),
        },
    }


def _row_matches(
    row: Mapping[str, Any],
    *,
    filters: Mapping[str, Any] | None,
    user_id: str | None,
) -> bool:
    if user_id is not None and row.get("user_id") != user_id:
        return False
    metadata = row.get("metadata")
    if not isinstance(metadata, Mapping):
        return False
    for key, expected in (filters or {}).items():
        actual = row.get("id") if key in {"id", "memory_id"} else metadata.get(key)
        if isinstance(expected, Mapping) and "in" in expected:
            if actual not in expected["in"]:
                return False
        elif actual != expected:
            return False
    return True


def _message_content(content: str | list[dict[str, str]]) -> str:
    if isinstance(content, str):
        normalized = content.strip()
    else:
        normalized = "\n".join(
            str(message.get("content", "")).strip()
            for message in content
            if str(message.get("content", "")).strip()
        )
    if not normalized:
        raise ValueError("PowerContext Source content must not be empty")
    return normalized


def _source_id(content: str, metadata: Mapping[str, Any], user_id: str) -> str:
    digest = sha256(
        _encode_entry(content, metadata, user_id).encode("utf-8")
    ).hexdigest()
    return f"smart-ev:{digest}"


def _json_mapping(value: Mapping[str, Any]) -> dict[str, JsonValue]:
    return json.loads(json.dumps(dict(value), ensure_ascii=False, default=str))
