from app.powermem.filtering import (
    fallback_read_limit,
    needs_server_filter_fallback,
    powermem_server_filters,
    records_matching_filters,
)
from app.powermem.mappers import powermem_hit_to_record
from app.services.acts.base import ActContext
from app.services.acts.localization import locale_for_context, localized
from app.services.lifecycle_service import LifecycleExecutionError, LifecycleService


def handle(context: ActContext, current_day: int, trace_id: str) -> dict:
    locale = locale_for_context(context)
    filters = {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "memory_kind": {
            "in": [
                "driving_preference",
                "emotional_preference",
                "temporary_context",
            ]
        },
    }
    memories = _list_lifecycle_memories(
        context,
        filters=filters,
        user_id=context.request.user_id or context.request.actor_id,
        limit=100,
    )
    service = LifecycleService(context.container.powermem_client)
    context.container.trace_service.create_trace(trace_id, context.request.session_id)
    try:
        run = service.run(memories, current_day)
    except LifecycleExecutionError as exc:
        exc.completed_operations = [
            {**entry, "trace_id": trace_id}
            for entry in exc.completed_operations
        ]
        exc.failed_operation = {
            **exc.failed_operation,
            "trace_id": trace_id,
        }
        exc.audit = [
            {**entry, "trace_id": trace_id} for entry in exc.audit
        ]
        exc.memories = memories
        for entry in exc.audit:
            _record_audit(context, trace_id, entry)
        exc.trace_id = trace_id
        raise
    completed_operations = [
        {**entry, "trace_id": trace_id}
        for entry in run.completed_operations
    ]
    audit = [{**entry, "trace_id": trace_id} for entry in run.audit]
    for entry in audit:
        _record_audit(context, trace_id, entry)
    return {
        "act_key": "Act 10",
        "assistant_reply": localized(
            locale,
            en="Lifecycle review completed.",
            zh="生命周期回顾已完成。",
        ),
        "current_day": current_day,
        "memory_hits": [memory.model_dump(mode="json") for memory in memories],
        "plan": [_plan_item(operation) for operation in run.plan],
        "completed_operations": completed_operations,
        "failed_operation": run.failed_operation,
        "audit": audit,
        "trace_id": trace_id,
        "operations": completed_operations,
    }


def _record_audit(context: ActContext, trace_id: str, entry: dict) -> None:
    context.container.journal_service.append(entry)
    context.container.trace_service.add_step(
        trace_id,
        name=f"lifecycle_{entry['type'].casefold()}",
        status=entry["result"],
        evidence=entry,
    )


def _plan_item(operation) -> dict:
    return {
        "type": operation.type,
        "memory_id": operation.memory_id,
        "memory_ids": [operation.memory_id],
        "before_status": operation.before_status,
        "after_status": operation.after_status,
    }


def _list_lifecycle_memories(
    context: ActContext,
    *,
    filters: dict,
    user_id: str,
    limit: int,
):
    rows = context.container.powermem_client.list_memories(
        filters=filters,
        user_id=user_id,
        limit=limit,
    )
    memories = records_matching_filters(
        (powermem_hit_to_record(row) for row in rows),
        filters,
    )
    has_temporary_context = any(
        memory.metadata.memory_kind == "temporary_context" for memory in memories
    )
    if not needs_server_filter_fallback(filters) or has_temporary_context:
        return memories[:limit]

    fallback_rows = context.container.powermem_client.list_memories(
        filters=powermem_server_filters(filters),
        user_id=user_id,
        limit=fallback_read_limit(limit),
    )
    fallback_memories = records_matching_filters(
        (powermem_hit_to_record(row) for row in fallback_rows),
        filters,
    )
    return _merge_unique(memories, fallback_memories)[:limit]


def _merge_unique(first, second):
    records = []
    seen = set()
    for record in [*first, *second]:
        if record.memory_id in seen:
            continue
        records.append(record)
        seen.add(record.memory_id)
    return records
