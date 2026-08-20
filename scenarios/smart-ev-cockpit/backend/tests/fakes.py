from app.domain.memory_models import MemoryMetadata, MemoryRecord


def memory_record(
    memory_id: str,
    *,
    content: str = "memory content",
    metadata_updates: dict | None = None,
) -> MemoryRecord:
    metadata = MemoryMetadata(
        memory_kind="temporary_context",
        created_at="2026-07-10T00:00:00Z",
    )
    if metadata_updates:
        metadata = metadata.model_copy(update=metadata_updates)
    return MemoryRecord(memory_id=memory_id, content=content, metadata=metadata)


class CrudPowerContext:
    def __init__(
        self,
        records: list[MemoryRecord] | None = None,
        *,
        delete_result: bool | dict = True,
    ):
        self.records = records or []
        self.delete_result = delete_result
        self.update_calls: list[dict] = []
        self.delete_calls: list[dict] = []
        self.get_all_calls: list[dict] = []

    def update(self, *, memory_id: str, content: str, metadata: dict) -> dict:
        call = {"memory_id": memory_id, "content": content, "metadata": metadata}
        self.update_calls.append(call)
        return {"success": True, **call}

    def delete(self, *, memory_id: str) -> bool | dict:
        self.delete_calls.append({"memory_id": memory_id})
        return self.delete_result

    def get_all(
        self,
        *,
        filters: dict | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> dict:
        self.get_all_calls.append(
            {"filters": filters, "user_id": user_id, "limit": limit}
        )
        return {
            "results": [
                {
                    "id": record.memory_id,
                    "memory": record.content,
                    "metadata": record.metadata.model_dump(mode="json"),
                }
                for record in self.records
            ]
        }
