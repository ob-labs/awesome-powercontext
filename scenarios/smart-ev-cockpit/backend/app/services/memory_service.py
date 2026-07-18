import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.domain.memory_models import MemoryMetadata, MemoryRecord
from app.powermem.client import PowerMemClient
from app.powermem.filtering import (
    fallback_read_limit,
    needs_server_filter_fallback,
    powermem_server_filters,
    record_matches_filters,
    records_matching_filters,
)
from app.powermem.mappers import powermem_hit_to_record
from app.services.memory_ordering import sort_memories

MIN_VECTOR_RELEVANCE_WINDOW = 20
VECTOR_RELEVANCE_LIMIT_MULTIPLIER = 4
MIN_VECTOR_SIMILARITY = 0.48


@dataclass(frozen=True)
class _SearchCandidate:
    record: MemoryRecord
    original_rank: int
    fts_rank: int | None
    vector_rank: int | None
    vector_similarity: float | None
    chat_created: bool


class MemoryService:
    def __init__(self, client: PowerMemClient):
        self.client = client

    def search(
        self,
        query: str,
        filters: dict,
        limit: int,
        user_id: str | None = None,
        prefer_recent_chat: bool = False,
    ) -> list[MemoryRecord]:
        if prefer_recent_chat:
            return self._search_recent_chat(
                query=query,
                filters=filters,
                limit=limit,
                user_id=user_id,
            )

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
            return _deduplicate_records(sort_memories(records))[:limit]

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
            return _deduplicate_records(sort_memories(records))[:limit]

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
        return _deduplicate_records(sort_memories(records))[:limit]

    def _search_recent_chat(
        self,
        *,
        query: str,
        filters: dict,
        limit: int,
        user_id: str | None,
    ) -> list[MemoryRecord]:
        hits = self.client.search_memories(
            query=query,
            filters=filters,
            limit=limit,
            user_id=user_id,
        )
        candidates = _semantic_candidates(hits, filters)
        server_filters = powermem_server_filters(filters)
        read_limit = fallback_read_limit(limit)

        if not candidates and needs_server_filter_fallback(filters):
            broad_hits = self.client.search_memories(
                query=query,
                filters=server_filters,
                limit=read_limit,
                user_id=user_id,
            )
            candidates = _semantic_candidates(broad_hits, filters)

        if candidates:
            return _rank_semantic_candidates(candidates, limit)

        if not self._client_supports_listing():
            return []

        rows = self.client.list_memories(
            filters=server_filters,
            user_id=user_id,
            limit=read_limit,
        )
        records = records_matching_filters(
            (powermem_hit_to_record(row) for row in rows),
            filters,
        )
        return _deduplicate_records(sort_memories(records))[:limit]

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


def _semantic_candidates(
    hits: list[dict],
    filters: dict,
) -> list[_SearchCandidate]:
    candidates: list[_SearchCandidate] = []
    for original_rank, hit in enumerate(hits):
        record = powermem_hit_to_record(hit)
        if not record_matches_filters(record, filters):
            continue
        raw_metadata = hit.get("metadata")
        metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
        raw_fusion = metadata.get("_fusion_info")
        fusion = raw_fusion if isinstance(raw_fusion, dict) else {}
        candidates.append(
            _SearchCandidate(
                record=record,
                original_rank=original_rank,
                fts_rank=_positive_rank(fusion.get("fts_rank")),
                vector_rank=_positive_rank(fusion.get("vector_rank")),
                vector_similarity=_unit_interval_score(
                    metadata.get("_vector_similarity")
                ),
                chat_created=any(
                    str(event_id).endswith(":chat")
                    for event_id in record.metadata.source_event_ids
                ),
            )
        )
    return candidates


def _positive_rank(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        return None
    return int(value)


def _unit_interval_score(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    score = float(value)
    if not 0.0 <= score <= 1.0:
        return None
    return score


def _rank_semantic_candidates(
    candidates: list[_SearchCandidate],
    limit: int,
) -> list[MemoryRecord]:
    unique = _unique_candidates(candidates)
    vector_window = max(
        MIN_VECTOR_RELEVANCE_WINDOW,
        limit * VECTOR_RELEVANCE_LIMIT_MULTIPLIER,
    )
    promoted = [
        candidate
        for candidate in unique
        if candidate.chat_created
        and (
            candidate.fts_rank is not None
            or (
                candidate.vector_rank is not None
                and candidate.vector_rank <= vector_window
                and candidate.vector_similarity is not None
                and candidate.vector_similarity >= MIN_VECTOR_SIMILARITY
            )
        )
    ]
    promoted.sort(
        key=lambda candidate: (
            -_created_at_timestamp(candidate.record.metadata.created_at),
            candidate.original_rank,
        )
    )
    promoted_ids = {candidate.record.memory_id for candidate in promoted}
    remaining = [
        candidate
        for candidate in unique
        if candidate.record.memory_id not in promoted_ids
        and (
            not candidate.chat_created
            or (candidate.fts_rank is None and candidate.vector_rank is None)
        )
    ]
    return [candidate.record for candidate in [*promoted, *remaining]][:limit]


def _unique_candidates(
    candidates: list[_SearchCandidate],
) -> list[_SearchCandidate]:
    unique: list[_SearchCandidate] = []
    seen: set[tuple[str, ...]] = set()
    for candidate in candidates:
        identity = _record_identity(candidate.record)
        if identity in seen:
            continue
        unique.append(candidate)
        seen.add(identity)
    return unique


def _created_at_timestamp(value: str | None) -> float:
    if not value:
        return 0.0
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.timestamp()


def _merge_unique(
    first: list[MemoryRecord],
    second: list[MemoryRecord],
) -> list[MemoryRecord]:
    records: list[MemoryRecord] = []
    seen: set[tuple[str, ...]] = set()
    for record in [*first, *second]:
        identity = _record_identity(record)
        if identity in seen:
            continue
        records.append(record)
        seen.add(identity)
    return records


def _deduplicate_records(records: list[MemoryRecord]) -> list[MemoryRecord]:
    unique: list[MemoryRecord] = []
    seen: set[tuple[str, ...]] = set()
    for record in records:
        identity = _record_identity(record)
        if identity in seen:
            continue
        unique.append(record)
        seen.add(identity)
    return unique


def _record_identity(record: MemoryRecord) -> tuple[str, ...]:
    normalized_content = _normalize_content(record.content)
    if not normalized_content:
        return ("memory_id", record.memory_id)
    metadata = record.metadata
    return (
        "content",
        metadata.scenario_id,
        metadata.vehicle_id,
        metadata.actor_id or "",
        metadata.seat_position or "",
        metadata.memory_kind,
        normalized_content,
    )


def _normalize_content(content: str) -> str:
    normalized = unicodedata.normalize("NFKC", content).casefold()
    return " ".join(normalized.split())
