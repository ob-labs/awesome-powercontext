from datetime import UTC, datetime

from app.domain.memory_models import MemoryRecord


def memory_rank(memory: MemoryRecord) -> tuple[float, float, str]:
    return (
        -memory.metadata.confidence,
        -_created_at_timestamp(memory.metadata.created_at),
        memory.memory_id,
    )


def sort_memories(memories: list[MemoryRecord]) -> list[MemoryRecord]:
    return sorted(memories, key=memory_rank)


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
