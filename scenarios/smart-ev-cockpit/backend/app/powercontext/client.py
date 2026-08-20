from typing import Any

from app.domain.memory_models import InferredMemoryMutation, MemoryMetadata, MemoryRecord


class PowerContextConnectionError(RuntimeError):
    pass


class PowerContextResponseError(RuntimeError):
    pass


class PowerContextIngestionError(RuntimeError):
    pass


class PowerContextClient:
    def __init__(self, memory: Any | None):
        self._memory = memory

    @property
    def is_connected(self) -> bool:
        return self._memory is not None

    def _require_memory(self) -> Any:
        if self._memory is None:
            raise PowerContextConnectionError(
                "PowerContext is not connected. Demo cannot continue in live mode."
            )
        return self._memory

    def require_memory(self) -> Any:
        return self._require_memory()

    def close(self) -> None:
        memory = self._memory
        self._memory = None
        close = getattr(memory, "close", None)
        if callable(close):
            close()

    def add_memory(
        self,
        content: str,
        metadata: MemoryMetadata,
        user_id: str,
        infer: bool = False,
    ) -> list[MemoryRecord]:
        memory = self._require_memory()
        result = memory.add(
            content,
            user_id=user_id,
            metadata=metadata.model_dump(mode="json"),
            infer=infer,
        )
        return _records_from_add_result(
            result,
            metadata=metadata,
        )

    def infer_memories(
        self,
        *,
        messages: list[dict[str, str]],
        user_id: str,
        metadata: dict,
    ) -> list[InferredMemoryMutation]:
        memory = self._require_memory()
        try:
            result = memory.add(
                messages,
                user_id=user_id,
                metadata=metadata,
                infer=True,
            )
        except Exception as exc:
            raise PowerContextIngestionError(
                f"PowerContext Source ingestion failed: {exc}"
            ) from exc
        return _mutations_from_infer_result(result)

    def search_memories(
        self,
        query: str,
        filters: dict,
        limit: int,
        user_id: str | None = None,
    ) -> list[dict]:
        memory = self._require_memory()
        result = memory.search(query=query, user_id=user_id, filters=filters, limit=limit)
        return list(result.get("results", []))

    def update_memory(self, memory_id: str, content: str, metadata: dict) -> dict:
        memory = self._require_memory()
        return memory.update(memory_id=memory_id, content=content, metadata=metadata)

    def delete_memory(self, memory_id: str) -> bool:
        memory = self._require_memory()
        result = memory.delete(memory_id=memory_id)
        if isinstance(result, bool):
            return result
        if isinstance(result, dict):
            if "deleted" in result:
                return bool(result["deleted"])
            if "success" in result:
                return bool(result["success"])
        return False

    def list_memories(
        self,
        filters: dict | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        memory = self._require_memory()
        result = memory.get_all(filters=filters, user_id=user_id, limit=limit)
        if isinstance(result, dict):
            return list(result.get("results", result.get("memories", [])))
        return list(result)


def _records_from_add_result(
    result: dict,
    metadata: MemoryMetadata,
) -> list[MemoryRecord]:
    if not isinstance(result, dict) or not isinstance(result.get("results"), list):
        raise PowerContextResponseError(
            "PowerContext returned an invalid ADD response: expected a results list"
        )

    rows = result["results"]
    if not rows:
        raise PowerContextResponseError(
            "PowerContext returned an invalid ADD response: results must not be empty"
        )

    records: list[MemoryRecord] = []
    for index, row in enumerate(rows):
        if (
            not isinstance(row, dict)
            or row.get("id") in (None, "")
            or not isinstance(row.get("memory"), str)
        ):
            raise PowerContextResponseError(
                "PowerContext returned an invalid ADD response: "
                f"results[{index}] requires id and memory"
            )
        records.append(
            MemoryRecord(
                memory_id=str(row["id"]),
                content=row["memory"],
                metadata=metadata,
            )
        )
    return records


def _mutations_from_infer_result(result: dict) -> list[InferredMemoryMutation]:
    if (
        not isinstance(result, dict)
        or "results" not in result
        or not isinstance(result["results"], list)
    ):
        raise PowerContextResponseError(
            "PowerContext returned an invalid Source ingestion response: "
            "expected a results list"
        )

    mutations: list[InferredMemoryMutation] = []
    for index, row in enumerate(result["results"]):
        if (
            not isinstance(row, dict)
            or row.get("id") in (None, "")
            or not isinstance(row.get("memory"), str)
            or not row["memory"].strip()
            or row.get("event") not in {"ADD", "UPDATE", "DELETE"}
        ):
            raise PowerContextResponseError(
                "PowerContext returned an invalid Source ingestion response: "
                f"results[{index}] requires id, memory, and ADD/UPDATE/DELETE event"
            )
        mutations.append(
            InferredMemoryMutation(
                event=row["event"],
                memory_id=str(row["id"]),
                content=row["memory"],
                previous_content=row.get("previous_memory"),
            )
        )
    return mutations
