from datetime import UTC, datetime

from app.domain.memory_models import MemoryMetadata
from app.services.test_data_generator import season_for_date

_SEASONAL_CABIN_SEED = {
    "spring": {"temp": 24, "seat_heat": 0},
    "summer": {"temp": 23, "seat_heat": 0},
    "autumn": {"temp": 24, "seat_heat": 1},
    "winter": {"temp": 26, "seat_heat": 2},
}


class SeedingService:
    def __init__(self, memory, generated_at: datetime | None = None):
        self.memory = memory
        self.generated_at = generated_at

    def seed(self) -> dict:
        specs = self._seed_specs(self.generated_at)
        if getattr(self.memory, "get_all", None) is None:
            specs = specs[:1]

        memory_ids: list[str] = []
        seeded = False
        for content, user_id, metadata in specs:
            source_event_id = metadata.source_event_ids[0]
            existing_memory_ids = self._existing_memory_ids(
                user_id=user_id,
                source_event_id=source_event_id,
            )
            if existing_memory_ids:
                memory_ids.extend(existing_memory_ids)
                continue
            result = self.memory.add(
                content,
                user_id=user_id,
                metadata=metadata.model_dump(mode="json"),
                infer=False,
            )
            rows = result.get("results", []) if isinstance(result, dict) else []
            memory_ids.extend(str(row.get("id", "")) for row in rows)
            seeded = True
        return {"seeded": seeded, "memory_ids": memory_ids}

    def _existing_memory_ids(self, *, user_id: str, source_event_id: str) -> list[str]:
        get_all = getattr(self.memory, "get_all", None)
        if get_all is None:
            return []

        result = get_all(
            user_id=user_id,
            filters={
                "scenario_id": "smart_ev_cockpit",
                "vehicle_id": "demo_vehicle_001",
                "source_event_ids": [source_event_id],
            },
            limit=1,
        )
        rows = result.get("results", result.get("memories", [])) if isinstance(result, dict) else []
        return [str(row.get("id", "")) for row in rows if row.get("id")]

    @staticmethod
    def _seed_specs(generated_at: datetime | None = None) -> list[tuple[str, str, MemoryMetadata]]:
        generation_time = _generation_time(generated_at)
        season = season_for_date(generation_time)
        cabin_seed = _SEASONAL_CABIN_SEED[season]
        common = {
            "created_at": generation_time.isoformat().replace("+00:00", "Z"),
            "lifecycle_status": "active",
        }
        return [
            (
                (
                    f"driver_primary prefers {cabin_seed['temp']}C and seat heat "
                    f"level {cabin_seed['seat_heat']} in {season}."
                ),
                "driver_primary",
                MemoryMetadata(
                    actor_id="driver_primary",
                    seat_position="front_left",
                    memory_kind="cabin_control_preference",
                    memory_dimension=["procedural"],
                    source_event_ids=[f"dlg_0001_{season}"],
                    season=season,
                    target_temp_c=cabin_seed["temp"],
                    seat_heat_level=cabin_seed["seat_heat"],
                    confidence=0.91,
                    hit_count=7,
                    retention_score=0.86,
                    **common,
                ),
            ),
            (
                "Rest mode capability is checked against un_support_funcs.",
                "driver_primary",
                MemoryMetadata(
                    actor_id="driver_primary",
                    seat_position="front_left",
                    memory_kind="vehicle_capability",
                    memory_dimension=["capability"],
                    source_event_ids=["seed_capability_rest_mode"],
                    capability_feature="rest_mode",
                    capability_supported=True,
                    capability_source_field="un_support_funcs",
                    **common,
                ),
            ),
            (
                "driver_primary prefers comfort drive mode for city routes.",
                "driver_primary",
                MemoryMetadata(
                    actor_id="driver_primary",
                    seat_position="front_left",
                    memory_kind="driving_preference",
                    memory_dimension=["procedural"],
                    source_event_ids=["seed_driving_comfort_mode"],
                    drive_mode="comfort",
                    **common,
                ),
            ),
            (
                "A masked restaurant destination is in the river district.",
                "driver_primary",
                MemoryMetadata(
                    actor_id="driver_primary",
                    seat_position="front_left",
                    memory_kind="location_episode",
                    memory_dimension=["episodic", "spatial"],
                    visibility="masked",
                    privacy_level="masked",
                    is_sensitive=True,
                    source_event_ids=["seed_location_restaurant"],
                    region="river district",
                    place_name="masked",
                    address="masked",
                    **common,
                ),
            ),
            (
                "The rear child prefers quiet bedtime stories.",
                "child_rear_left",
                MemoryMetadata(
                    actor_id="child_rear_left",
                    seat_position="rear_left",
                    memory_kind="media_preference",
                    memory_dimension=["preference", "family"],
                    visibility="masked",
                    privacy_level="masked",
                    source_event_ids=["seed_media_child_sleep"],
                    media_volume=18,
                    content_category="bedtime_story",
                    **common,
                ),
            ),
            (
                "Child media volume must not exceed the safe cap.",
                "child_rear_left",
                MemoryMetadata(
                    actor_id="child_rear_left",
                    seat_position="rear_left",
                    memory_kind="safety_policy",
                    memory_dimension=["policy"],
                    visibility="hidden",
                    privacy_level="hidden",
                    source_event_ids=["seed_safety_child_volume"],
                    max_media_volume=16,
                    **common,
                ),
            ),
            (
                "An anniversary preference suggests a calm dinner.",
                "driver_primary",
                MemoryMetadata(
                    actor_id="driver_primary",
                    seat_position="front_left",
                    memory_kind="relationship_event",
                    memory_dimension=["episodic", "relationship"],
                    visibility="masked",
                    privacy_level="masked",
                    is_sensitive=True,
                    source_event_ids=["seed_relationship_anniversary"],
                    anniversary_date="2020-07-10",
                    relationship_recommendation="calm_dinner",
                    recommendation_hint="calm dinner",
                    **common,
                ),
            ),
            (
                (
                    "driver_primary has a temporary pickup reminder that expires "
                    "before scenario day 90."
                ),
                "driver_primary",
                MemoryMetadata(
                    actor_id="driver_primary",
                    seat_position="front_left",
                    memory_kind="temporary_context",
                    memory_dimension=["working"],
                    memory_layer="short_term",
                    source_event_ids=["seed_temporary_day90_cleanup_v2"],
                    valid_until="2026-01-15T00:00:00Z",
                    retention_policy="expire_after_valid_until",
                    retention_score=0.72,
                    **common,
                ),
            ),
        ]


def _generation_time(generated_at: datetime | None) -> datetime:
    if generated_at is None:
        return datetime.now(UTC)
    if generated_at.tzinfo is None:
        return generated_at.replace(tzinfo=UTC)
    return generated_at.astimezone(UTC)
