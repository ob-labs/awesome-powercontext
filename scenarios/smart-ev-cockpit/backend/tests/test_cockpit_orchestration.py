from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.data.csv_snapshot_loader import SnapshotResult
from app.dependencies import AppContainer
from app.domain.memory_models import MemoryMetadata, MemoryRecord
from app.main import create_app
from app.powercontext.client import PowerContextClient
from app.services.chat_history_service import ChatHistoryService


def _record(memory_id: str, kind: str, **updates) -> MemoryRecord:
    metadata = MemoryMetadata(
        actor_id=updates.pop("actor_id", "driver_primary"),
        seat_position=updates.pop("seat_position", "front_left"),
        memory_kind=kind,
        created_at="2026-01-01T00:00:00Z",
    ).model_copy(update=updates)
    return MemoryRecord(
        memory_id=memory_id,
        content=f"structured {kind} record",
        metadata=metadata,
    )


class OrchestrationPowerContext:
    def __init__(self):
        self.records = [
            _record(
                "cabin",
                "cabin_control_preference",
                target_temp_c=26,
                seat_heat_level=2,
            ),
            _record("drive", "driving_preference", drive_mode="comfort"),
            _record(
                "capability",
                "vehicle_capability",
                capability_feature="rest_mode",
                capability_supported=True,
            ),
            _record("location", "location_episode", region="river district"),
            _record(
                "media",
                "media_preference",
                actor_id="child_rear_left",
                seat_position="rear_left",
                media_volume=18,
                content_category="bedtime_story",
            ),
            _record(
                "policy",
                "safety_policy",
                actor_id="child_rear_left",
                seat_position="rear_left",
                max_media_volume=16,
            ),
            _record(
                "relationship",
                "relationship_event",
                relationship_recommendation="calm_dinner",
            ),
            _record(
                "charging",
                "charging_preference",
                charging_strategy="nearest_available",
            ),
            _record(
                "emotion",
                "emotional_preference",
                emotional_tone="calm",
            ),
            _record(
                "temporary",
                "temporary_context",
                retention_score=0.8,
            ),
        ]
        self.add_calls = []
        self.search_calls = []
        self.get_all_calls = []
        self.update_calls = []

    def add(self, content, **kwargs):
        self.add_calls.append({"content": content, **kwargs})
        if kwargs.get("infer"):
            return {"results": []}
        return {"results": [{"id": "added-preference", "memory": content}]}

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        filters = kwargs["filters"]
        kinds = filters.get("memory_kind")
        allowed = (
            None
            if kinds is None
            else set(kinds.get("in", [])) if isinstance(kinds, dict) else {kinds}
        )
        actor_id = filters.get("actor_id")
        seat_position = filters.get("seat_position")
        rows = [
            record
            for record in self.records
            if (allowed is None or record.metadata.memory_kind in allowed)
            and (actor_id is None or record.metadata.actor_id == actor_id)
            and (seat_position is None or record.metadata.seat_position == seat_position)
        ]
        return {"results": [_raw(record) for record in rows]}

    def get_all(self, **kwargs):
        self.get_all_calls.append(kwargs)
        return {"results": [_raw(record) for record in self.records]}

    def update(self, *, memory_id, content, metadata):
        self.update_calls.append(
            {"memory_id": memory_id, "content": content, "metadata": metadata}
        )
        return {"success": True}

    def delete(self, *, memory_id):
        return True


class MetadataFilterLimitedOrchestrationPowerContext(OrchestrationPowerContext):
    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        filters = kwargs["filters"]
        if set(filters) - {"scenario_id", "vehicle_id"}:
            return {"results": []}
        return {"results": [_raw(record) for record in self.records]}

    def get_all(self, **kwargs):
        self.get_all_calls.append(kwargs)
        filters = kwargs.get("filters") or {}
        if set(filters) - {"scenario_id", "vehicle_id"}:
            return {"results": []}
        return {"results": [_raw(record) for record in self.records]}


class SnapshotLoader:
    def load_vehicle_profile(self):
        return SnapshotResult(
            {
                "vehicle_id": "demo_vehicle_001",
                "unsupported_features": [],
            },
            "masked_vehicle_csv",
            [],
        )

    def load_telemetry(self):
        return SnapshotResult(
            {"soc": 62, "range_km": 305, "outside_temp_c": 6},
            "synthetic_fallback",
            [],
        )


def _raw(record: MemoryRecord) -> dict:
    return {
        "id": record.memory_id,
        "memory": record.content,
        "metadata": record.metadata.model_dump(mode="json"),
    }


def _client(tmp_path: Path, memory=None, llm_client=None):
    raw_memory = memory or OrchestrationPowerContext()
    container = AppContainer(
        powercontext_client=PowerContextClient(raw_memory),
        llm_client=llm_client,
        chat_history_service=ChatHistoryService(tmp_path / "chat.sqlite3"),
    )
    container.csv_snapshot_loader = SnapshotLoader()
    return TestClient(create_app(container=container)), raw_memory


@pytest.mark.parametrize(
    ("act_key", "text", "actor_id", "seat_position", "operation_type"),
    [
        ("Act 1", "冬天上车一般 26C，座椅加热 2 档。", "driver_primary", "front_left", "ADD"),
        ("Act 2", "I feel cold.", "driver_primary", "front_left", "SEARCH"),
        ("Act 3", "Use my previous comfort setup.", "driver_primary", "front_left", "SEARCH"),
        ("Act 4", "Does this vehicle support rest mode?", "driver_primary", "front_left", "SEARCH"),
        (
            "Act 5",
            "Take me to the restaurant from last Friday.",
            "driver_primary",
            "front_left",
            "SEARCH",
        ),
        (
            "Act 6",
            "Play something for the child to sleep.",
            "child_rear_left",
            "rear_left",
            "SEARCH",
        ),
        ("Act 7", "Any plan for tonight?", "driver_primary", "front_left", "SEARCH"),
        ("Act 8", "Driving mode suggestion.", "driver_primary", "front_left", "SEARCH"),
        ("Act 10", "Lifecycle and privacy.", "driver_primary", "front_left", "UPDATE"),
    ],
)
def test_all_explicit_acts_return_normalized_contract(
    tmp_path, act_key, text, actor_id, seat_position, operation_type
):
    client, _ = _client(tmp_path)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "act_key": act_key,
            "actor_id": actor_id,
            "seat_position": seat_position,
            "text": text,
            "session_id": f"session-{act_key}",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["act_key"] == act_key
    assert operation_type in {operation["type"] for operation in body["operations"]}
    assert {
        "act_key",
        "data_source",
        "operations",
        "memory_hits",
        "selected_memory_ids",
        "vehicle_state",
        "vehicle_state_diff",
        "recommendations",
        "privacy_report",
        "evidence",
        "trace_id",
    } <= body.keys()
    assert {
        "request",
        "privacy",
        "data_source",
        "operations",
        "memory_hits",
        "decision",
        "vehicle_action",
        "latency_ms",
    } <= body["evidence"].keys()
    hit_ids = {hit["memory_id"] for hit in body["memory_hits"]}
    if act_key == "Act 1":
        assert body["selected_memory_ids"] == ["added-preference"]
    else:
        assert set(body["selected_memory_ids"]) <= hit_ids


def test_act_1_saves_preference_and_applies_cabin_state(tmp_path):
    client, memory = _client(tmp_path)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "act_key": "Act 1",
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "text": "我夏天上车一般 23C，座椅加热 0 档。",
            "session_id": "act-1-climate-link",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assistant_reply"] == "已保存并应用你的座舱偏好。"
    assert body["vehicle_state"]["hvac"]["front_left_target_temp"] == 23
    assert body["vehicle_state"]["seat_heat"]["front_left"] == 0
    assert {
        "field": "hvac.front_left_target_temp",
        "before": 22,
        "after": 23,
    } in body["vehicle_state_diff"]
    assert body["evidence"]["vehicle_action"]["patch"] == {
        "hvac": {"front_left_target_temp": 23},
        "seat_heat": {"front_left": 0},
    }
    assert memory.add_calls[0]["metadata"]["target_temp_c"] == 23


def test_act_2_applies_remembered_temperature_from_reported_hot_cabin_context(tmp_path):
    memory = OrchestrationPowerContext()
    memory.records[0] = _record(
        "cabin",
        "cabin_control_preference",
        target_temp_c=23,
        seat_heat_level=0,
    )
    client, _ = _client(tmp_path, memory=memory)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "act_key": "Act 2",
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "text": "车里有点热。",
            "session_id": "act-2-hot-cabin",
            "vehicle_context": {"hvac_target_temp_c": 28.5},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert {
        "field": "hvac.front_left_target_temp",
        "before": 28.5,
        "after": 23,
    } in body["vehicle_state_diff"]
    assert body["vehicle_state"]["hvac"]["front_left_target_temp"] == 23
    assert body["evidence"]["request"]["vehicle_context"] == {
        "hvac_target_temp_c": 28.5
    }


def test_explicit_act_wins_compatibility_and_unknown_unkeyed_text_uses_chat(tmp_path):
    client, _ = _client(tmp_path)
    explicit = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "act_key": "Act 4",
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "text": "I feel cold.",
            "session_id": "explicit",
        },
    )
    compatible = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "text": "I feel cold.",
            "session_id": "compatible",
        },
    )
    unknown = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "text": "completely unknown free text",
            "session_id": "unknown",
        },
    )

    assert explicit.status_code == 200
    assert explicit.json()["act_key"] == "Act 4"
    assert compatible.status_code == 200
    assert compatible.json()["act_key"] == "Act 2"
    assert unknown.status_code == 200
    unknown_body = unknown.json()
    assert unknown_body["act_key"] == "Chat"
    assert unknown_body["operations"][0]["result"] == "memory_chat_fallback"
    assert unknown_body["memory_hits"]


def test_act_9_utter_requires_vehicle_event_endpoint(tmp_path):
    client, _ = _client(tmp_path)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "act_key": "Act 9",
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "text": "Proactive care.",
            "session_id": "act-9-utter",
        },
    )

    assert response.status_code == 422
    assert "/events/vehicle" in response.json()["detail"]


def test_scripted_flow_never_adds_raw_dialogue_to_powercontext(tmp_path):
    client, memory = _client(tmp_path)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "act_key": "Act 2",
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "text": "I feel cold.",
            "session_id": "no-long-term-dialogue",
        },
    )

    assert response.status_code == 200
    assert memory.add_calls == []
    history = client.get(
        "/api/scenarios/smart-ev-cockpit/chat-history",
        params={"session_id": "no-long-term-dialogue"},
    ).json()["messages"]
    assert [message["role"] for message in history] == ["user", "assistant"]


def test_normalized_evidence_omits_empty_optional_sections(tmp_path):
    client, _ = _client(tmp_path)

    body = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "act_key": "Act 2",
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "text": "I feel cold.",
            "session_id": "evidence",
        },
    ).json()

    assert "recommendations" not in body["evidence"]
    assert "lifecycle" not in body["evidence"]
    assert "audit" not in body["evidence"]


def test_llm_failure_does_not_change_deterministic_reply(tmp_path):
    class FailingLlm:
        def chat(self, **kwargs):
            raise AssertionError("scripted orchestration must not call chat")

    client, _ = _client(tmp_path, llm_client=FailingLlm())

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "act_key": "Act 2",
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "text": "I feel cold.",
            "session_id": "deterministic",
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["assistant_reply"]
        == "I set the driver zone temperature to 26C and set seat heat to level 2."
    )


def test_memories_forwards_filters_and_projects_private_content(tmp_path):
    memory = OrchestrationPowerContext()
    memory.records = [
        _record(
            "private-location",
            "location_episode",
            visibility="hidden",
            is_sensitive=True,
            lifecycle_status="archived",
        )
    ]
    client, _ = _client(tmp_path, memory=memory)

    response = client.get(
        "/api/scenarios/smart-ev-cockpit/memories",
        params={
            "actor_id": "driver_primary",
            "memory_kind": "location_episode",
            "lifecycle_status": "archived",
        },
    )

    assert response.status_code == 200
    assert memory.get_all_calls == [
        {
            "filters": {
                "scenario_id": "smart_ev_cockpit",
                "vehicle_id": "demo_vehicle_001",
                "actor_id": "driver_primary",
                "memory_kind": "location_episode",
                "lifecycle_status": "archived",
            },
            "user_id": "driver_primary",
            "limit": 100,
        }
    ]
    projected = response.json()["memories"][0]
    assert projected["content"] == "Masked location_episode memory"
    assert "structured location_episode record" not in response.text


def test_memories_requires_actor_id_and_defensively_isolates_cross_actor_rows(tmp_path):
    memory = OrchestrationPowerContext()
    memory.records = [
        _record("driver-memory", "driving_preference"),
        _record(
            "passenger-memory",
            "driving_preference",
            actor_id="passenger_front",
            seat_position="front_right",
        ),
    ]
    client, _ = _client(tmp_path, memory=memory)

    missing = client.get("/api/scenarios/smart-ev-cockpit/memories")
    isolated = client.get(
        "/api/scenarios/smart-ev-cockpit/memories",
        params={"actor_id": "driver_primary"},
    )

    assert missing.status_code == 422
    assert [row["memory_id"] for row in isolated.json()["memories"]] == [
        "driver-memory"
    ]
    assert memory.get_all_calls[0]["user_id"] == "driver_primary"


def test_memories_recovers_when_powercontext_does_not_support_metadata_filters(tmp_path):
    memory = MetadataFilterLimitedOrchestrationPowerContext()
    memory.records = [
        _record(
            "driver-location",
            "location_episode",
            lifecycle_status="archived",
        ),
        _record(
            "passenger-location",
            "location_episode",
            actor_id="passenger_front",
            seat_position="front_right",
            lifecycle_status="archived",
        ),
    ]
    client, _ = _client(tmp_path, memory=memory)

    response = client.get(
        "/api/scenarios/smart-ev-cockpit/memories",
        params={
            "actor_id": "driver_primary",
            "memory_kind": "location_episode",
            "lifecycle_status": "archived",
        },
    )

    assert response.status_code == 200
    assert [row["memory_id"] for row in response.json()["memories"]] == [
        "driver-location"
    ]
    assert memory.get_all_calls[0]["filters"] == {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "actor_id": "driver_primary",
        "memory_kind": "location_episode",
        "lifecycle_status": "archived",
    }
    assert memory.get_all_calls[1]["filters"] == {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
    }


def test_vehicle_event_returns_normalized_low_soc_diff_projection_and_journal(tmp_path):
    memory = OrchestrationPowerContext()
    memory.records = [
        _record(
            "private-charging",
            "charging_preference",
            charging_strategy="nearest_available",
            visibility="hidden",
            is_sensitive=True,
        )
    ]
    client, _ = _client(tmp_path, memory=memory)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/events/vehicle",
        json={"soc": 9, "range_km": 42},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["act_key"] == "Act 9"
    assert body["evidence"]["decision"]["reason_codes"] == ["critical_soc"]
    assert {
        "field": "soc",
        "before": 62,
        "after": 9,
    } in body["vehicle_state_diff"]
    assert body["memory_hits"][0]["content"] == "Masked charging_preference memory"
    assert "structured charging_preference record" not in response.text
    assert client.get(
        "/api/scenarios/smart-ev-cockpit/state"
    ).json()["recent_operations"][-1]["trace_id"] == body["trace_id"]


def test_lifecycle_endpoint_returns_normalized_projection_and_journal(tmp_path):
    memory = OrchestrationPowerContext()
    memory.records = [
        _record(
            "private-temporary",
            "temporary_context",
            visibility="hidden",
            is_sensitive=True,
            retention_score=0.8,
        )
    ]
    client, _ = _client(tmp_path, memory=memory)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/lifecycle/run",
        json={"current_day": 90},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["act_key"] == "Act 10"
    assert body["operations"][0]["type"] == "UPDATE"
    assert body["memory_hits"][0]["content"] == "Masked temporary_context memory"
    assert "structured temporary_context record" not in response.text
    assert body["evidence"]["lifecycle"]["current_day"] == 90
    assert client.get(
        "/api/scenarios/smart-ev-cockpit/state"
    ).json()["recent_operations"][-1]["trace_id"] == body["trace_id"]


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        (
            "post",
            "/api/scenarios/smart-ev-cockpit/events/vehicle",
            {"json": {"soc": 9, "range_km": 42}},
        ),
        (
            "post",
            "/api/scenarios/smart-ev-cockpit/lifecycle/run",
            {"json": {"current_day": 90}},
        ),
        (
            "get",
            "/api/scenarios/smart-ev-cockpit/memories",
            {"params": {"actor_id": "driver_primary"}},
        ),
    ],
)
def test_live_endpoints_return_503_when_powercontext_is_disconnected(
    tmp_path, method, path, kwargs
):
    container = AppContainer(
        powercontext_client=PowerContextClient(None),
        chat_history_service=ChatHistoryService(tmp_path / "chat.sqlite3"),
    )
    client = TestClient(create_app(container=container), raise_server_exceptions=False)
    before = container.vehicle_state_service.current_state()

    response = getattr(client, method)(path, **kwargs)

    assert response.status_code == 503
    assert "PowerContext is not connected" in response.json()["detail"]
    assert container.vehicle_state_service.current_state() == before
