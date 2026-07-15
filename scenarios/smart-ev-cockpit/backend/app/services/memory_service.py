from app.domain.memory_models import MemoryMetadata, MemoryRecord
from app.powermem.client import PowerMemClient
from app.powermem.filtering import (
    fallback_read_limit,
    needs_server_filter_fallback,
    powermem_server_filters,
    records_matching_filters,
)
from app.powermem.mappers import powermem_hit_to_record
from app.services.memory_ordering import sort_memories


class MemoryService:
    def __init__(self, client: PowerMemClient):
        self.client = client

    def search(
        self,
        query: str,
        filters: dict,
        limit: int,
        user_id: str | None = None,
    ) -> list[MemoryRecord]:
        hits = self.client.search_memories(
            query=query,
            filters=filters,
            limit=limit,
            user_id=user_id,
        )
        records = records_matching_filters(
            (powermem_hit_to_record(hit) for hit in hits),
            filters,
        )
        if not needs_server_filter_fallback(filters):
            return sort_memories(records)[:limit]

        server_filters = powermem_server_filters(filters)
        read_limit = fallback_read_limit(limit)
        if not records:
            broad_hits = self.client.search_memories(
                query=query,
                filters=server_filters,
                limit=read_limit,
                user_id=user_id,
            )
            records = _merge_unique(
                records,
                records_matching_filters(
                    (powermem_hit_to_record(hit) for hit in broad_hits),
                    filters,
                ),
            )
        if not self._client_supports_listing():
            return sort_memories(records)[:limit]

        rows = self.client.list_memories(
            filters=server_filters,
            user_id=user_id,
            limit=read_limit,
        )
        records = _merge_unique(
            records,
            records_matching_filters(
                (powermem_hit_to_record(row) for row in rows),
                filters,
            ),
        )
        return sort_memories(records)[:limit]

    def add(
        self,
        content: str,
        metadata: MemoryMetadata,
        user_id: str,
        infer: bool = False,
    ) -> list[MemoryRecord]:
        return self.client.add_memory(
            content=content,
            metadata=metadata,
            user_id=user_id,
            infer=infer,
        )

    def update(self, memory: MemoryRecord, metadata_updates: dict) -> dict:
        metadata = memory.metadata.model_copy(update=metadata_updates)
        return self.client.update_memory(
            memory.memory_id,
            content=memory.content,
            metadata=metadata.model_dump(mode="json"),
        )

    def archive(self, memory: MemoryRecord) -> dict:
        return self.update(memory, {"lifecycle_status": "archived"})

    def delete(self, memory_id: str) -> bool:
        return self.client.delete_memory(memory_id)

    def _client_supports_listing(self) -> bool:
        return self.client.is_connected and hasattr(
            self.client.require_memory(),
            "get_all",
        )


def _merge_unique(
    first: list[MemoryRecord],
    second: list[MemoryRecord],
) -> list[MemoryRecord]:
    records: list[MemoryRecord] = []
    seen: set[str] = set()
    for record in [*first, *second]:
        if record.memory_id in seen:
            continue
        records.append(record)
        seen.add(record.memory_id)
    return records
