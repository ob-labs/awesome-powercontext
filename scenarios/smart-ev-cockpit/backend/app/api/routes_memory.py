from fastapi import APIRouter, HTTPException, Request

from app.powermem.client import PowerMemConnectionError
from app.powermem.filtering import (
    fallback_read_limit,
    needs_server_filter_fallback,
    powermem_server_filters,
    record_matches_filters,
    records_matching_filters,
)
from app.powermem.mappers import powermem_hit_to_record
from app.privacy.projection import project_memory_for_frontend

router = APIRouter(prefix="/api/scenarios/smart-ev-cockpit")


@router.get("/memories")
def memories(
    request: Request,
    actor_id: str,
    user_id: str | None = None,
    memory_kind: str | None = None,
    lifecycle_status: str | None = None,
    limit: int = 100,
) -> dict:
    effective_user_id = user_id or actor_id
    filters = {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
    }
    filters["actor_id"] = actor_id
    if memory_kind is not None:
        filters["memory_kind"] = memory_kind
    if lifecycle_status is not None:
        filters["lifecycle_status"] = lifecycle_status
    try:
        client = request.app.state.container.powermem_client
        rows = client.list_memories(
            filters=filters,
            user_id=effective_user_id,
            limit=limit,
        )
        records = records_matching_filters(
            (powermem_hit_to_record(row) for row in rows),
            filters,
        )
        if not records and needs_server_filter_fallback(filters):
            rows = client.list_memories(
                filters=powermem_server_filters(filters),
                user_id=effective_user_id,
                limit=fallback_read_limit(limit),
            )
            records = records_matching_filters(
                (powermem_hit_to_record(row) for row in rows),
                filters,
            )
    except PowerMemConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "memories": [
            project_memory_for_frontend(record)
            for record in records[:limit]
        ]
    }


@router.delete("/memories/{memory_id}")
def delete_memory(
    memory_id: str,
    actor_id: str,
    request: Request,
    user_id: str | None = None,
) -> dict:
    client = request.app.state.container.powermem_client
    effective_user_id = user_id or actor_id
    filters = {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "actor_id": actor_id,
        "memory_id": memory_id,
    }
    try:
        rows = client.list_memories(
            filters=filters,
            user_id=effective_user_id,
            limit=100,
        )
        owned = _has_matching_memory(rows, filters)
        if not owned and needs_server_filter_fallback(filters):
            rows = client.list_memories(
                filters=powermem_server_filters(filters),
                user_id=effective_user_id,
                limit=fallback_read_limit(100),
            )
            owned = _has_matching_memory(rows, filters)
        if not owned:
            raise HTTPException(status_code=404, detail="Memory not found")
        deleted = client.delete_memory(memory_id)
    except PowerMemConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"memory_id": memory_id, "deleted": deleted}


def _has_matching_memory(rows: list[dict], filters: dict) -> bool:
    return any(
        record_matches_filters(powermem_hit_to_record(row), filters)
        for row in rows
    )
