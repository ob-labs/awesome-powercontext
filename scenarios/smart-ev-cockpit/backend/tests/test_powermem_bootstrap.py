from datetime import UTC, datetime

from app.dependencies import build_default_container
from app.main import create_app
from app.services.seeding_service import SeedingService


class RecordingPowerMem:
    def __init__(self):
        self.add_calls = []

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


class FailingSeedPowerMem:
    def add(self, content, user_id=None, metadata=None, infer=False):
        raise RuntimeError("seed write failed")


class ExistingSeedPowerMem:
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


class RecordingOpenAIClient:
    def __init__(self):
        self.with_options_calls = []
        self.configured_client = object()

    def with_options(self, **options):
        self.with_options_calls.append(options)
        return self.configured_client


class ConfigurablePowerMem(RecordingPowerMem):
    def __init__(self):
        super().__init__()
        self.embedding = type("Embedding", (), {})()
        self.embedding.client = RecordingOpenAIClient()


def test_create_app_does_not_bootstrap_powermem_by_default(monkeypatch):
    def fail_bootstrap():
        raise AssertionError("PowerMem bootstrap should not run")

    monkeypatch.setattr("app.main.build_default_container", fail_bootstrap)

    app = create_app()

    assert app.state.container.powermem_client.is_connected is False


def test_default_container_initializes_powermem(monkeypatch):
    created = RecordingPowerMem()

    def fake_create_memory():
        return created

    monkeypatch.setattr("app.dependencies.create_memory", fake_create_memory)

    container = build_default_container()

    assert container.powermem_client.is_connected is True


def test_default_container_limits_embedding_request_duration(monkeypatch):
    created = ConfigurablePowerMem()
    original_client = created.embedding.client

    monkeypatch.setattr("app.dependencies.create_memory", lambda: created)

    container = build_default_container()

    assert container.powermem_client.is_connected is True
    assert original_client.with_options_calls == [
        {"timeout": 30.0, "max_retries": 0}
    ]
    assert created.embedding.client is original_client.configured_client


def test_default_container_disables_powermem_when_seed_fails(monkeypatch):
    def fake_create_memory():
        return FailingSeedPowerMem()

    monkeypatch.setattr("app.dependencies.create_memory", fake_create_memory)

    container = build_default_container()

    assert container.powermem_client.is_connected is False


def test_seeding_service_writes_summer_cabin_memory():
    memory = RecordingPowerMem()

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
    memory = ExistingSeedPowerMem()

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
