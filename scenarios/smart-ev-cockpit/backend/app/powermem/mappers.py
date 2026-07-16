from app.domain.memory_models import MemoryMetadata, MemoryRecord


def powermem_hit_to_record(hit: dict) -> MemoryRecord:
    metadata = MemoryMetadata.model_validate(hit.get("metadata", {}))
    return MemoryRecord(
        memory_id=str(hit.get("id", hit.get("memory_id", ""))),
        content=str(hit.get("memory", hit.get("content", ""))),
        metadata=metadata,
    )
