import logging
import unicodedata
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock, Thread
from time import sleep
from typing import Any, Literal
from uuid import uuid4

from app.domain.memory_models import MemoryLocale
from app.services.test_data_generator import (
    GeneratedMemoryRow,
    generate_dataset_id,
    generate_memory_rows,
    read_memory_jsonl,
    write_memory_jsonl,
)

DATA_ROOT = Path(__file__).resolve().parents[3] / "data" / "synthetic" / "generated"
CLEAR_BATCH_SIZE = 1000
DEFAULT_IMPORT_MAX_WORKERS = 3
RATE_LIMIT_MAX_RETRIES = 6
RATE_LIMIT_INITIAL_BACKOFF_SECONDS = 1.0
RATE_LIMIT_MAX_BACKOFF_SECONDS = 30.0
LOGICALLY_UNIQUE_MEMORY_KINDS = frozenset({"vehicle_capability"})
JobState = Literal[
    "idle", "generated", "importing", "imported", "deleting", "deleted", "failed"
]

logger = logging.getLogger(__name__)


@dataclass
class TestDataStatus:
    state: JobState = "idle"
    dataset_id: str | None = None
    dataset_path: str | None = None
    locale: MemoryLocale = "en"
    generated_count: int = 0
    imported_count: int = 0
    deleted_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    last_error: str | None = None

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


class TestDataService:
    __test__ = False

    def __init__(
        self,
        data_root: Path = DATA_ROOT,
        *,
        rate_limit_max_retries: int = RATE_LIMIT_MAX_RETRIES,
        retry_sleep: Callable[[float], None] = sleep,
    ):
        self.data_root = data_root
        self._rate_limit_max_retries = max(0, rate_limit_max_retries)
        self._retry_sleep = retry_sleep
        self._lock = Lock()
        self._status = TestDataStatus()
        self._job_thread: Thread | None = None

    def generate_dataset(
        self,
        count: int = 1200,
        seed: int = 42,
        locale: MemoryLocale = "en",
        actor_user_ids: dict[str, str] | None = None,
    ) -> TestDataStatus:
        generated_at = datetime.now(UTC)
        dataset_id = generate_dataset_id(
            count=count,
            seed=seed,
            locale=locale,
            generated_at=generated_at,
            unique_suffix=uuid4().hex[:8],
        )
        rows = generate_memory_rows(
            count=count,
            seed=seed,
            dataset_id=dataset_id,
            locale=locale,
            actor_user_ids=actor_user_ids,
            generated_at=generated_at,
        )
        dataset_path = self._dataset_path(dataset_id)
        write_memory_jsonl(dataset_path, rows)
        self._status = TestDataStatus(
            state="generated",
            dataset_id=dataset_id,
            dataset_path=str(dataset_path),
            locale=locale,
            generated_count=len(rows),
        )
        return self._status

    def import_dataset(
        self,
        memory,
        dataset_id: str,
        apply: bool,
        limit: int | None = None,
        max_workers: int = DEFAULT_IMPORT_MAX_WORKERS,
        actor_user_ids: dict[str, str] | None = None,
    ) -> TestDataStatus:
        rows = self._read_dataset(dataset_id)
        rows_to_import = rows[:limit] if limit is not None else rows
        if apply:
            existing_count = self._existing_dataset_count(memory, dataset_id)
            if existing_count > 0:
                return self._mark_dataset_already_imported(
                    dataset_id=dataset_id,
                    generated_count=len(rows_to_import),
                    existing_count=existing_count,
                )

        self._set_status(TestDataStatus(
            state="importing",
            dataset_id=dataset_id,
            dataset_path=str(self._dataset_path(dataset_id)),
            locale=self._dataset_locale(rows_to_import),
            generated_count=len(rows_to_import),
        ))
        self._run_import_rows(
            memory=memory,
            rows=rows_to_import,
            apply=apply,
            max_workers=max_workers,
            actor_user_ids=actor_user_ids,
        )
        return self.status()

    def start_import_dataset(
        self,
        memory,
        dataset_id: str,
        apply: bool,
        limit: int | None = None,
        max_workers: int = DEFAULT_IMPORT_MAX_WORKERS,
        actor_user_ids: dict[str, str] | None = None,
    ) -> TestDataStatus:
        if not apply:
            return self.import_dataset(
                memory=memory,
                dataset_id=dataset_id,
                apply=False,
                limit=limit,
                max_workers=max_workers,
                actor_user_ids=actor_user_ids,
            )

        current_status = self.status()
        if (
            current_status.state == "importing"
            and current_status.dataset_id == dataset_id
        ):
            return current_status

        rows = self._read_dataset(dataset_id)
        rows_to_import = rows[:limit] if limit is not None else rows
        existing_count = self._existing_dataset_count(memory, dataset_id)
        if existing_count > 0:
            return self._mark_dataset_already_imported(
                dataset_id=dataset_id,
                generated_count=len(rows_to_import),
                existing_count=existing_count,
            )

        self._set_status(TestDataStatus(
            state="importing",
            dataset_id=dataset_id,
            dataset_path=str(self._dataset_path(dataset_id)),
            locale=self._dataset_locale(rows_to_import),
            generated_count=len(rows_to_import),
        ))
        self._job_thread = Thread(
            target=self._run_import_rows,
            kwargs={
                "memory": memory,
                "rows": rows_to_import,
                "apply": True,
                "max_workers": max_workers,
                "actor_user_ids": actor_user_ids,
            },
            daemon=True,
        )
        self._job_thread.start()
        return self.status()

    def wait_for_current_job(self, timeout: float | None = None) -> TestDataStatus:
        if self._job_thread is not None:
            self._job_thread.join(timeout=timeout)
        return self.status()

    def clear_all_memories(self, memory, apply: bool) -> TestDataStatus:
        current_status = self.status()
        self._set_status(TestDataStatus(
            state="deleting",
            locale=current_status.locale,
        ))

        if not apply:
            offset = 0
            while True:
                rows = self._memory_rows(memory.get_all(
                    user_id=None,
                    filters=None,
                    limit=CLEAR_BATCH_SIZE,
                    offset=offset,
                ))
                self._increment_status("skipped_count", len(rows))
                if len(rows) < CLEAR_BATCH_SIZE:
                    break
                offset += len(rows)
            self._update_status(state="deleted")
            return self.status()

        deleted_ids: set[str] = set()
        while True:
            try:
                rows = self._memory_rows(memory.get_all(
                    user_id=None,
                    filters=None,
                    limit=CLEAR_BATCH_SIZE,
                    offset=0,
                ))
            except Exception as exc:  # pragma: no cover - exercised through live API
                self._increment_status("failed_count")
                self._update_status(last_error=str(exc))
                break

            if not rows:
                break

            deleted_in_batch = 0
            for row in rows:
                memory_id = str(row.get("id", ""))
                if not memory_id:
                    self._increment_status("failed_count")
                    self._update_status(last_error="PowerContext returned a memory without an id.")
                    continue
                if memory_id in deleted_ids:
                    self._increment_status("failed_count")
                    self._update_status(
                        last_error=f"Memory {memory_id} remained after deletion."
                    )
                    continue
                try:
                    if memory.delete(memory_id=memory_id):
                        deleted_ids.add(memory_id)
                        deleted_in_batch += 1
                        self._increment_status("deleted_count")
                    else:
                        self._increment_status("failed_count")
                        self._update_status(
                            last_error=f"PowerContext did not delete memory {memory_id}."
                        )
                except Exception as exc:  # pragma: no cover - exercised through live API
                    self._increment_status("failed_count")
                    self._update_status(last_error=str(exc))

            if deleted_in_batch == 0:
                break

        final_status = self.status()
        self._update_status(
            state="deleted" if final_status.failed_count == 0 else "failed"
        )
        return self.status()

    def delete_dataset(self, memory, dataset_id: str, apply: bool) -> TestDataStatus:
        status = TestDataStatus(
            state="deleting",
            dataset_id=dataset_id,
            dataset_path=str(self._dataset_path(dataset_id)),
            locale=self._dataset_locale_from_file(dataset_id),
        )
        self._set_status(status)
        result = memory.get_all(
            user_id=None,
            filters={"dataset_id": dataset_id},
            limit=10000,
        )
        rows = self._memory_rows(result)

        for row in rows:
            memory_id = str(row.get("id", ""))
            if not memory_id:
                continue
            if not apply:
                status.skipped_count += 1
                continue
            try:
                if memory.delete(memory_id=memory_id):
                    status.deleted_count += 1
            except Exception as exc:  # pragma: no cover - exercised through live API
                status.failed_count += 1
                status.last_error = str(exc)

        status.state = "deleted" if status.failed_count == 0 else "failed"
        return status

    def status(self) -> TestDataStatus:
        with self._lock:
            return TestDataStatus(**self._status.model_dump())

    def dataset_exists(self, dataset_id: str) -> bool:
        return self._dataset_path(dataset_id).exists()

    def _dataset_path(self, dataset_id: str) -> Path:
        return self.data_root / f"{dataset_id}.jsonl"

    def _read_dataset(self, dataset_id: str):
        dataset_path = self._dataset_path(dataset_id)
        if not dataset_path.exists():
            raise FileNotFoundError(str(dataset_path))
        return read_memory_jsonl(dataset_path)

    def _memory_rows(self, result) -> list:
        if isinstance(result, dict):
            return result.get("results", result.get("memories", []))
        return result

    def _existing_dataset_count(self, memory, dataset_id: str) -> int:
        result = memory.get_all(
            user_id=None,
            filters={"dataset_id": dataset_id},
            limit=10000,
        )
        return len(self._memory_rows(result))

    def _mark_dataset_already_imported(
        self,
        dataset_id: str,
        generated_count: int,
        existing_count: int,
    ) -> TestDataStatus:
        return self._set_status(TestDataStatus(
            state="imported",
            dataset_id=dataset_id,
            dataset_path=str(self._dataset_path(dataset_id)),
            locale=self._dataset_locale_from_file(dataset_id),
            generated_count=generated_count,
            imported_count=existing_count,
            skipped_count=generated_count,
        ))

    def _dataset_locale(self, rows) -> MemoryLocale:
        if not rows:
            return "en"
        locale = rows[0].metadata.get("locale", "en")
        return "zh" if locale == "zh" else "en"

    def _dataset_locale_from_file(self, dataset_id: str) -> MemoryLocale:
        try:
            return self._dataset_locale(self._read_dataset(dataset_id))
        except FileNotFoundError:
            return "en"

    def _set_status(self, status: TestDataStatus) -> TestDataStatus:
        with self._lock:
            self._status = status
            return TestDataStatus(**self._status.model_dump())

    def _update_status(self, **updates) -> TestDataStatus:
        with self._lock:
            for key, value in updates.items():
                setattr(self._status, key, value)
            return TestDataStatus(**self._status.model_dump())

    def _increment_status(self, field_name: str, amount: int = 1) -> TestDataStatus:
        with self._lock:
            setattr(self._status, field_name, getattr(self._status, field_name) + amount)
            return TestDataStatus(**self._status.model_dump())

    def _run_import_rows(
        self,
        memory,
        rows,
        apply: bool,
        max_workers: int,
        actor_user_ids: dict[str, str] | None,
    ) -> None:
        if not apply:
            self._update_status(skipped_count=len(rows), state="imported")
            return

        rows, duplicate_count = self._deduplicate_import_rows(memory, rows)
        if duplicate_count:
            self._increment_status("skipped_count", duplicate_count)
        if not rows:
            self._update_status(state="imported")
            return

        worker_count = max(1, min(max_workers, len(rows) or 1))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            for batch_start in range(0, len(rows), worker_count):
                batch = rows[batch_start : batch_start + worker_count]
                futures = [
                    executor.submit(
                        self._add_row_with_rate_limit_retry,
                        memory,
                        row,
                        actor_user_ids,
                    )
                    for row in batch
                ]
                batch_failed = False
                for future in as_completed(futures):
                    try:
                        future.result()
                        self._increment_status("imported_count")
                    except Exception as exc:  # pragma: no cover - exercised through live API
                        batch_failed = True
                        self._increment_status("failed_count")
                        self._update_status(last_error=str(exc))

                if batch_failed:
                    attempted_count = batch_start + len(batch)
                    self._increment_status("skipped_count", len(rows) - attempted_count)
                    break

        final_status = self.status()
        self._update_status(
            state="imported" if final_status.failed_count == 0 else "failed"
        )

    def _deduplicate_import_rows(
        self,
        memory,
        rows: list[GeneratedMemoryRow],
    ) -> tuple[list[GeneratedMemoryRow], int]:
        existing_keys = self._existing_logical_memory_keys(memory, rows)
        seen = set(existing_keys)
        unique_rows: list[GeneratedMemoryRow] = []
        duplicate_count = 0

        for row in rows:
            key = _logical_memory_key(row.content, row.metadata)
            if key is not None and key in seen:
                duplicate_count += 1
                continue
            unique_rows.append(row)
            if key is not None:
                seen.add(key)

        return unique_rows, duplicate_count

    def _existing_logical_memory_keys(
        self,
        memory,
        rows: list[GeneratedMemoryRow],
    ) -> set[tuple[str, ...]]:
        candidate_keys = {
            key
            for row in rows
            if (key := _logical_memory_key(row.content, row.metadata)) is not None
        }
        if not candidate_keys:
            return set()

        first_metadata = rows[0].metadata
        filters = {
            "scenario_id": first_metadata.get("scenario_id", "smart_ev_cockpit"),
            "vehicle_id": first_metadata.get("vehicle_id", "demo_vehicle_001"),
        }
        try:
            result = memory.get_all(user_id=None, filters=filters, limit=10000)
        except Exception as exc:  # pragma: no cover - live backend safeguard
            logger.warning("Could not preflight logical memory duplicates: %s", exc)
            return set()

        existing_keys: set[tuple[str, ...]] = set()
        for row in self._memory_rows(result):
            metadata = row.get("metadata") if isinstance(row, dict) else None
            if not isinstance(metadata, dict):
                continue
            content = row.get("memory", row.get("content", ""))
            key = _logical_memory_key(str(content), metadata)
            if key is not None:
                existing_keys.add(key)
        return existing_keys

    def _add_row_with_rate_limit_retry(
        self,
        memory,
        row,
        actor_user_ids: dict[str, str] | None,
    ) -> None:
        for retry_index in range(self._rate_limit_max_retries + 1):
            try:
                memory.add(
                    row.content,
                    user_id=self._row_user_id(row, actor_user_ids),
                    metadata=row.metadata,
                    infer=False,
                )
                return
            except Exception as exc:
                if (
                    not self._is_rate_limit_error(exc)
                    or retry_index >= self._rate_limit_max_retries
                ):
                    raise

                delay = min(
                    RATE_LIMIT_INITIAL_BACKOFF_SECONDS * (2 ** retry_index),
                    RATE_LIMIT_MAX_BACKOFF_SECONDS,
                )
                retry_after = self._retry_after_seconds(exc)
                if retry_after is not None:
                    delay = max(delay, retry_after)
                logger.warning(
                    "Memory backend rate limited; retrying in %.1fs (%d/%d)",
                    delay,
                    retry_index + 1,
                    self._rate_limit_max_retries,
                )
                self._retry_sleep(delay)

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        if getattr(exc, "status_code", None) == 429:
            return True
        response = getattr(exc, "response", None)
        return getattr(response, "status_code", None) == 429

    @staticmethod
    def _retry_after_seconds(exc: Exception) -> float | None:
        response = getattr(exc, "response", None)
        headers = getattr(response, "headers", None)
        if headers is None:
            return None
        retry_after = headers.get("retry-after")
        if retry_after is None:
            return None
        try:
            parsed = float(retry_after)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    def _row_user_id(self, row, actor_user_ids: dict[str, str] | None) -> str:
        if actor_user_ids is None:
            return row.user_id
        actor_id = row.metadata.get("actor_id")
        if not isinstance(actor_id, str):
            return row.user_id
        return actor_user_ids.get(actor_id, row.user_id)


def _logical_memory_key(content: str, metadata: dict[str, Any]) -> tuple[str, ...] | None:
    memory_kind = str(metadata.get("memory_kind", ""))
    if memory_kind not in LOGICALLY_UNIQUE_MEMORY_KINDS:
        return None

    capability_feature = _normalize_text(str(metadata.get("capability_feature", "")))
    identity = capability_feature or _normalize_text(content)
    if not identity:
        return None
    return (
        str(metadata.get("scenario_id", "")),
        str(metadata.get("vehicle_id", "")),
        str(metadata.get("actor_id", "")),
        str(metadata.get("seat_position", "")),
        memory_kind,
        identity,
    )


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(normalized.split())
