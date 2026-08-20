from pydantic import BaseModel, Field


class MemorySearchQuery(BaseModel):
    query: str
    user_id: str | None = None
    filters: dict = Field(default_factory=dict)
    limit: int = 5


def build_cold_cabin_query(
    actor_id: str,
    seat_position: str,
    user_id: str | None = None,
) -> MemorySearchQuery:
    return MemorySearchQuery(
        query=f"winter cold cabin comfort preference for {actor_id} {seat_position}",
        user_id=user_id or actor_id,
        filters={
            "scenario_id": "smart_ev_cockpit",
            "vehicle_id": "demo_vehicle_001",
            "memory_kind": {
                "in": [
                    "cabin_control_preference",
                    "emotional_preference",
                    "temporary_context",
                ]
            },
        },
        limit=5,
    )


def build_act_02_query(
    actor_id: str,
    seat_position: str,
    user_id: str | None = None,
) -> MemorySearchQuery:
    return MemorySearchQuery(
        query=f"cold cabin preferences and safety policy for {actor_id} {seat_position}",
        user_id=user_id or actor_id,
        filters={
            "scenario_id": "smart_ev_cockpit",
            "vehicle_id": "demo_vehicle_001",
            "actor_id": actor_id,
            "seat_position": seat_position,
            "memory_kind": {
                "in": ["cabin_control_preference", "safety_policy"]
            },
        },
        limit=10,
    )


def build_routine_query(
    actor_id: str,
    seat_position: str,
    user_id: str | None = None,
) -> MemorySearchQuery:
    return MemorySearchQuery(
        query=f"previous cabin and driving routine for {actor_id} {seat_position}",
        user_id=user_id or actor_id,
        filters={
            "scenario_id": "smart_ev_cockpit",
            "vehicle_id": "demo_vehicle_001",
            "actor_id": actor_id,
            "seat_position": seat_position,
            "memory_kind": {
                "in": ["cabin_control_preference", "driving_preference"]
            },
        },
        limit=10,
    )


def build_general_cockpit_query(
    utterance: str,
    actor_id: str,
    seat_position: str,
    user_id: str | None = None,
) -> MemorySearchQuery:
    return MemorySearchQuery(
        query=utterance,
        user_id=user_id or actor_id,
        filters={
            "scenario_id": "smart_ev_cockpit",
            "vehicle_id": "demo_vehicle_001",
            "actor_id": actor_id,
            "seat_position": seat_position,
        },
        limit=5,
    )
