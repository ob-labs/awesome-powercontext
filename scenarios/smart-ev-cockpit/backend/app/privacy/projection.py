from typing import Any

from app.domain.memory_models import MemoryRecord


def project_memory_for_frontend(memory: MemoryRecord) -> dict[str, Any]:
    hidden_fields: list[str] = []
    content = memory.content

    if memory.metadata.visibility in {"masked", "hidden"} or memory.metadata.is_sensitive:
        content = f"Masked {memory.metadata.memory_kind} memory"
        hidden_fields.append("sensitive_content")

    if memory.metadata.visibility == "deleted":
        content = "Deleted memory tombstone"
        hidden_fields.append("deleted_content")

    return {
        "memory_id": memory.memory_id,
        "content": content,
        "memory_kind": memory.metadata.memory_kind,
        "visibility": memory.metadata.visibility,
        "lifecycle_status": memory.metadata.lifecycle_status,
        "actor_id": memory.metadata.actor_id,
        "source_event_ids": memory.metadata.source_event_ids,
        "hidden_fields": hidden_fields,
    }
