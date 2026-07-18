from datetime import UTC, datetime

from app.domain.memory_models import MemoryMetadata, MemoryRecord


def powermem_hit_to_record(hit: dict) -> MemoryRecord:
    metadata = MemoryMetadata.model_validate(_metadata_with_created_at(hit))
    return MemoryRecord(
        memory_id=str(hit.get("id", hit.get("memory_id", ""))),
        content=str(hit.get("memory", hit.get("content", ""))),
        metadata=metadata,
    )


def _metadata_with_created_at(hit: dict) -> dict:
    metadata = dict(hit.get("metadata") or {})
    created_at = hit.get("created_at")
    if "created_at" not in metadata and created_at is not None:
        if isinstance(created_at, datetime):
            created_at = created_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
        metadata["created_at"] = str(created_at)
    return metadata
