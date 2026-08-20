from datetime import UTC, datetime

from app.dependencies import build_default_container
from app.main import create_app
from app.services.seeding_service import SeedingService


class RecordingPowerContext:
    def __init__(self):
        self.add_calls = []
        self.closed = False

    def add(self, content, user_id=None, metadata=None, infer=False):
        self.add_calls.append(
            {
                "content": content,
                "user_id": user_id,
                "metadata": metadata,
                "infer": infer,
            }
        )
        return {
            "results": [
                {
                    "id": "mem_seed_cabin",
                    "memory": content,
                    "metadata": metadata,
                }
            ]
        }

    def close(self):
        self.closed = True


class FailingSeedPowerContext:
    def __init__(self):
        self.closed = False

    def add(self, content, user_id=None, metadata=None, infer=False):
        raise RuntimeError("seed write failed")

    def close(self):
        self.closed = True


class ExistingSeedPowerContext:
    def __init__(self):
        self.add_calls = []
        self.get_all_calls = []

    def get_all(self, user_id=None, filters=None, limit=100):
        self.get_all_calls.append(
            {"user_id": user_id, "filters": filters, "limit": limit}
        )
        if filters.get("source_event_ids") == ["dlg_0001_summer"]:
            return {"results": [{"id": "mem_existing_summer"}]}
        return {"results": []}

    def add(self, content, user_id=None, metadata=None, infer=False):
        self.add_calls.append(
            {
                "content": content,
                "user_id": user_id,
                "metadata": metadata,
                "infer": infer,
            }
        )
        return {"results": []}


def test_create_app_does_not_bootstrap_powercontext_by_default(monkeypatch):
    def fail_bootstrap():
        raise AssertionError("PowerContext bootstrap should not run")

    monkeypatch.setattr("app.main.build_default_container", fail_bootstrap)

    app = create_app()

    assert app.state.container.powercontext_client.is_connected is False


def test_default_container_initializes_powercontext(monkeypatch):
    created = RecordingPowerContext()

    monkeypatch.setattr(
        "app.dependencies.EmbeddedPowerContextMemory",
        lambda **_kwargs: created,
    )

    container = build_default_container()

    assert container.powercontext_client.is_connected is True


def test_default_container_disables_powercontext_when_seed_fails(monkeypatch):
    created = FailingSeedPowerContext()

    monkeypatch.setattr(
        "app.dependencies.EmbeddedPowerContextMemory",
        lambda **_kwargs: created,
    )

    container = build_default_container()

    assert container.powercontext_client.is_connected is False
    assert created.closed is True


def test_seeding_service_writes_summer_cabin_memory():
    memory = RecordingPowerContext()

    result = SeedingService(
        memory,
        generated_at=datetime(2026, 7, 12, 8, 10, tzinfo=UTC),
    ).seed()

    assert result["seeded"] is True
    assert result["memory_ids"] == ["mem_seed_cabin"]
    assert memory.add_calls == [
        {
            "content": "driver_primary prefers 23C and seat heat level 0 in summer.",
            "user_id": "driver_primary",
            "metadata": {
                "scenario_id": "smart_ev_cockpit",
                "vehicle_id": "demo_vehicle_001",
                "actor_id": "driver_primary",
                "seat_position": "front_left",
                "season": "summer",
                "target_temp_c": 23.0,
                "seat_heat_level": 0,
                "session_id": None,
                "trace_id": None,
                "memory_kind": "cabin_control_preference",
                "locale": "en",
                "memory_dimension": ["procedural"],
                "memory_layer": "long_term",
                "privacy_level": "public_demo",
                "visibility": "public_demo",
                "source_event_ids": ["dlg_0001_summer"],
                "confidence": 0.91,
                "hit_count": 7,
                "created_at": "2026-07-12T08:10:00Z",
                "last_accessed_at": None,
                "valid_from": None,
                "valid_until": None,
                "retention_policy": "reinforce_on_hit",
                "retention_score": 0.86,
                "lifecycle_status": "active",
                "is_sensitive": False,
            },
            "infer": False,
        }
    ]


def test_seeding_service_reuses_existing_seasonal_cabin_memory():
    memory = ExistingSeedPowerContext()

    result = SeedingService(
        memory,
        generated_at=datetime(2026, 7, 12, 8, 10, tzinfo=UTC),
    ).seed()

    assert result == {"seeded": True, "memory_ids": ["mem_existing_summer"]}
    assert {
        call["metadata"]["source_event_ids"][0] for call in memory.add_calls
    } == {
        "seed_capability_rest_mode",
        "seed_driving_comfort_mode",
        "seed_location_restaurant",
        "seed_media_child_sleep",
        "seed_safety_child_volume",
        "seed_relationship_anniversary",
        "seed_temporary_day90_cleanup_v2",
    }
    assert len(memory.get_all_calls) == 8
    assert all(
        list(call["filters"]) == [
            "scenario_id",
            "vehicle_id",
            "source_event_ids",
        ]
        for call in memory.get_all_calls
    )
