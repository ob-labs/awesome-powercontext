from fastapi.testclient import TestClient

from app.data.csv_snapshot_loader import SnapshotResult
from app.dependencies import AppContainer
from app.domain.memory_models import MemoryMetadata, MemoryRecord
from app.domain.scenario_models import ActRequest
from app.main import create_app
from app.powermem.client import PowerMemClient
from app.services.acts import act_08_driving, act_09_proactive
from app.services.acts.base import ActContext
from tests.fakes import CrudPowerMem


def _record(memory_id: str, kind: str, **metadata_updates) -> MemoryRecord:
    metadata = MemoryMetadata(
        actor_id="driver_primary",
        seat_position="front_left",
        memory_kind=kind,
        created_at="2026-07-10T00:00:00Z",
    ).model_copy(update=metadata_updates)
    return MemoryRecord(memory_id=memory_id, content=f"content for {memory_id}", metadata=metadata)


class SearchPowerMem(CrudPowerMem):
    def __init__(self, records=None):
        super().__init__(records)
        self.search_calls = []

    def search(self, query, user_id=None, filters=None, limit=5):
        self.search_calls.append(
            {"query": query, "user_id": user_id, "filters": filters, "limit": limit}
        )
        return {
            "results": [
                {
                    "id": record.memory_id,
                    "memory": record.content,
                    "metadata": record.metadata.model_dump(mode="json"),
                    "score": record.metadata.confidence,
                }
                for record in self.records
            ]
        }


class LimitingSearchPowerMem(SearchPowerMem):
    def search(self, query, user_id=None, filters=None, limit=5):
        self.search_calls.append(
            {"query": query, "user_id": user_id, "filters": filters, "limit": limit}
        )
        return {
            "results": [
                {
                    "id": record.memory_id,
                    "memory": record.content,
                    "metadata": record.metadata.model_dump(mode="json"),
                    "score": record.metadata.confidence,
                }
                for record in self.records[:limit]
            ]
        }


class StubLoader:
    def __init__(self, telemetry: dict, source: str):
        self.result = SnapshotResult(telemetry, source, [])

    def load_telemetry(self):
        return self.result


def _context(records, *, soc=62, outside_temp_c=6, source="test_telemetry"):
    fake = SearchPowerMem(records)
    container = AppContainer(powermem_client=PowerMemClient(fake))
    container.csv_snapshot_loader = StubLoader(
        {"soc": soc, "range_km": 305, "outside_temp_c": outside_temp_c}, source
    )
    request = ActRequest(
        act_key="Act 8",
        actor_id="driver_primary",
        seat_position="front_left",
        text="driving mode suggestion",
        session_id="session-1",
    )
    return ActContext(request=request, container=container), fake


def test_act_8_uses_preference_and_reports_actual_telemetry_source():
    context, fake = _context(
        [
            _record(
                "drive-1",
                "driving_preference",
                drive_mode="comfort",
                confidence=0.8,
            )
        ],
        source="soa_csv",
    )

    result = act_08_driving.handle(context)

    assert result.data_source == "soa_csv"
    assert result.recommendations[0].metadata["drive_mode"] == "comfort"
    assert result.selected_memory_ids == ["drive-1"]
    assert fake.search_calls[0]["filters"]["memory_kind"] == {
        "in": ["driving_preference", "emotional_preference"]
    }


def test_act_8_low_soc_prefers_safe_eco_mode_when_a_preference_exists():
    context, _ = _context(
        [_record("drive-1", "driving_preference", drive_mode="sport")],
        soc=19,
    )

    result = act_08_driving.handle(context)

    assert result.recommendations[0].metadata["drive_mode"] == "eco"
    assert "low_soc" in result.reason_codes


def test_act_8_does_not_invent_mode_without_driving_preference():
    context, _ = _context(
        [_record("emotion-1", "emotional_preference", emotional_tone="reassuring")]
    )

    result = act_08_driving.handle(context)

    assert result.recommendations == []
    assert result.selected_memory_ids == []
    assert result.reason_codes == ["no_applicable_memory"]


def test_act_8_searches_past_legacy_rows_without_drive_mode():
    fake = LimitingSearchPowerMem(
        [
            _record(
                f"legacy-drive-{index}",
                "driving_preference",
                confidence=0.96 - index * 0.001,
            )
            for index in range(12)
        ]
        + [_record("drive-used", "driving_preference", drive_mode="comfort", confidence=0.8)]
    )
    container = AppContainer(powermem_client=PowerMemClient(fake))
    container.csv_snapshot_loader = StubLoader(
        {"soc": 62, "range_km": 305, "outside_temp_c": 6}, "test_telemetry"
    )
    context = ActContext(
        request=ActRequest(
            act_key="Act 8",
            actor_id="driver_primary",
            seat_position="front_left",
            text="driving mode suggestion",
            session_id="session-1",
        ),
        container=container,
    )

    result = act_08_driving.handle(context)

    assert fake.search_calls[0]["limit"] > 12
    assert result.selected_memory_ids == ["drive-used"]
    assert result.recommendations[0].metadata["drive_mode"] == "comfort"


def test_act_8_orders_equal_confidence_hits_by_memory_id():
    context, _ = _context(
        [
            _record("drive-b", "driving_preference", drive_mode="comfort", confidence=0.9),
            _record("drive-a", "driving_preference", drive_mode="eco", confidence=0.9),
        ]
    )

    result = act_08_driving.handle(context)

    assert [hit.memory_id for hit in result.memory_hits] == ["drive-a", "drive-b"]
    assert result.selected_memory_ids == ["drive-a"]


def test_act_8_missing_soc_returns_no_action_with_actual_source():
    context, _ = _context(
        [_record("drive-1", "driving_preference", drive_mode="comfort")],
        soc=None,
        source="synthetic_fallback",
    )

    result = act_08_driving.handle(context)

    assert result.recommendations == []
    assert result.selected_memory_ids == []
    assert result.reason_codes == ["telemetry_missing"]
    assert result.data_source == "synthetic_fallback"


def _act_9(records, soc):
    fake = SearchPowerMem(records)
    container = AppContainer(powermem_client=PowerMemClient(fake))
    request = ActRequest(
        act_key="Act 9",
        actor_id="driver_primary",
        seat_position="front_left",
        text="proactive care",
        session_id="session-1",
    )
    result = act_09_proactive.handle(
        ActContext(request=request, container=container),
        {"soc": soc, "range_km": 80},
    )
    return result, container


def test_act_9_uses_fixed_low_and_critical_soc_boundaries():
    records = [_record("drive-1", "driving_preference", drive_mode="eco")]

    at_20, _ = _act_9(records, 20)
    at_19, _ = _act_9(records, 19)
    at_10, _ = _act_9(records, 10)
    at_9, _ = _act_9(records, 9)

    assert "low_soc" not in at_20.reason_codes
    assert "low_soc" in at_19.reason_codes
    assert "critical_soc" not in at_10.reason_codes
    assert "critical_soc" in at_9.reason_codes


def test_act_9_emotional_tone_changes_words_not_safety_recommendation():
    calm, _ = _act_9(
        [
            _record("drive-1", "driving_preference", drive_mode="eco"),
            _record("emotion-1", "emotional_preference", emotional_tone="calm"),
        ],
        9,
    )
    direct, _ = _act_9(
        [
            _record("drive-1", "driving_preference", drive_mode="eco"),
            _record("emotion-2", "emotional_preference", emotional_tone="direct"),
        ],
        9,
    )

    assert calm.assistant_reply != direct.assistant_reply
    assert calm.recommendations[0].model_dump() == direct.recommendations[0].model_dump()


def test_act_9_searches_charging_driving_emotional_and_selects_only_used_records():
    result, _ = _act_9(
        [
            _record(
                "charging-1",
                "charging_preference",
                charging_strategy="nearest_available",
            ),
            _record("drive-1", "driving_preference", drive_mode="eco"),
            _record("emotion-1", "emotional_preference", emotional_tone="calm"),
        ],
        9,
    )

    assert result.operations[0].filters["memory_kind"] == {
        "in": [
            "charging_preference",
            "driving_preference",
            "emotional_preference",
        ]
    }
    assert result.selected_memory_ids == ["charging-1", "emotion-1"]
    assert result.recommendations[0].metadata["charging_strategy"] == "nearest_available"


def test_act_9_handler_decides_without_mutating_vehicle_state():
    result, container = _act_9(
        [_record("drive-1", "driving_preference", drive_mode="eco")],
        9,
    )

    assert container.vehicle_state_service.current_state()["soc"] == 62
    assert result.vehicle_patch == {"soc": 9, "range_km": 80}
    assert [operation.type for operation in result.operations] == ["SEARCH"]


def test_vehicle_event_endpoint_returns_complete_act_9_and_mutates_state():
    fake = SearchPowerMem([_record("drive-1", "driving_preference", drive_mode="eco")])
    app = create_app(container=AppContainer(powermem_client=PowerMemClient(fake)))
    client = TestClient(app)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/events/vehicle",
        json={"soc": 19, "range_km": 76},
    )

    assert response.status_code == 200
    assert response.json()["act_key"] == "Act 9"
    assert [operation["type"] for operation in response.json()["operations"]] == [
        "SEARCH",
        "VEHICLE_PATCH",
    ]
    assert client.get("/api/scenarios/smart-ev-cockpit/state").json()["vehicle_state"]["soc"] == 19


def test_vehicle_event_endpoint_localizes_chinese_act_9_text():
    fake = SearchPowerMem([_record("drive-1", "driving_preference", drive_mode="eco")])
    app = create_app(container=AppContainer(powermem_client=PowerMemClient(fake)))
    client = TestClient(app)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/events/vehicle",
        json={"soc": 9, "range_km": 42, "text": "触发低电量主动关怀。"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["act_key"] == "Act 9"
    assert body["assistant_reply"] == (
        "当前电量 9%，剩余续航 42 公里。"
        "请立即导航到可到达的充电站，请确认是否开始导航。"
    )
    assert body["recommendations"][0]["title"] == "电池安全建议"
    assert body["recommendations"][0]["summary"] == "请立即导航到可到达的充电站。"
    assert body["recommendations"][0]["action_policy"] == "confirm"


def test_vehicle_event_confirmation_executes_charging_navigation_without_act_5():
    fake = SearchPowerMem(
        [
            _record(
                "charging-1",
                "charging_preference",
                charging_strategy="nearest_available",
            ),
            _record("location-1", "location_episode", region="张江科学城"),
        ]
    )
    app = create_app(container=AppContainer(powermem_client=PowerMemClient(fake)))
    client = TestClient(app)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/events/vehicle",
        json={
            "soc": 9,
            "range_km": 42,
            "text": "确认导航",
            "confirm_navigation": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["act_key"] == "Act 9"
    assert body["assistant_reply"] == "已确认，开始导航到最近可用的充电站。"
    assert body["recommendations"][0]["type"] == "charging_navigation"
    assert body["recommendations"][0]["action_policy"] == "execute"
    assert body["vehicle_state"]["navigation"] == {
        "mode": "map",
        "status": "active",
        "destination": {
            "area_scope": "category",
            "destination_type": "charging_station",
            "selection_strategy": "nearest_available",
        },
        "destination_label": "最近可用的充电站",
    }
    assert "张江科学城" not in response.text


class FailedSearchPowerMem(SearchPowerMem):
    def search(self, query, user_id=None, filters=None, limit=5):
        raise RuntimeError("search failed")


def test_vehicle_event_search_failure_does_not_mutate_state():
    container = AppContainer(
        powermem_client=PowerMemClient(FailedSearchPowerMem())
    )
    client = TestClient(
        create_app(container=container),
        raise_server_exceptions=False,
    )
    before = container.vehicle_state_service.current_state()

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/events/vehicle",
        json={"soc": 9, "range_km": 42},
    )

    assert response.status_code == 500
    assert container.vehicle_state_service.current_state() == before


def test_vehicle_event_endpoint_rejects_unknown_fields():
    app = create_app(
        container=AppContainer(powermem_client=PowerMemClient(SearchPowerMem()))
    )

    response = TestClient(app).post(
        "/api/scenarios/smart-ev-cockpit/events/vehicle",
        json={"soc": 19, "range_km": 76, "unknown": True},
    )

    assert response.status_code == 422


def test_lifecycle_endpoint_validates_and_mutates_scenario_day():
    fake = SearchPowerMem([])
    app = create_app(container=AppContainer(powermem_client=PowerMemClient(fake)))
    client = TestClient(app)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/lifecycle/run",
        json={"current_day": 90},
    )

    assert response.status_code == 200
    assert response.json()["act_key"] == "Act 10"
    assert client.get("/api/scenarios/smart-ev-cockpit/state").json()["scenario_day"] == 90
    assert client.post(
        "/api/scenarios/smart-ev-cockpit/lifecycle/run",
        json={"current_day": 91},
    ).status_code == 422


def test_lifecycle_endpoint_localizes_chinese_act_10_text():
    fake = SearchPowerMem([])
    app = create_app(container=AppContainer(powermem_client=PowerMemClient(fake)))
    client = TestClient(app)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/lifecycle/run",
        json={"current_day": 90, "text": "执行第 90 天生命周期回顾。"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["act_key"] == "Act 10"
    assert body["assistant_reply"] == "生命周期回顾已完成。"


def test_lifecycle_trace_id_is_unique_for_each_run():
    fake = SearchPowerMem([])
    client = TestClient(
        create_app(container=AppContainer(powermem_client=PowerMemClient(fake)))
    )

    first = client.post(
        "/api/scenarios/smart-ev-cockpit/lifecycle/run",
        json={"current_day": 90},
    ).json()
    second = client.post(
        "/api/scenarios/smart-ev-cockpit/lifecycle/run",
        json={"current_day": 90},
    ).json()

    assert first["trace_id"] != second["trace_id"]
    assert first["trace_id"] == first["lifecycle"]["trace_id"]
    assert first["trace_id"] == first["evidence"]["lifecycle"]["trace_id"]
    assert second["trace_id"] == second["lifecycle"]["trace_id"]


class FailedUpdatePowerMem(SearchPowerMem):
    def update(self, *, memory_id: str, content: str, metadata: dict):
        self.update_calls.append(
            {"memory_id": memory_id, "content": content, "metadata": metadata}
        )
        return None


def test_lifecycle_failure_response_includes_trace_and_partial_progress():
    fake = FailedUpdatePowerMem(
        [
            _record(
                "temp-1",
                "temporary_context",
                retention_score=0.8,
                visibility="hidden",
                is_sensitive=True,
            )
        ]
    )
    client = TestClient(
        create_app(container=AppContainer(powermem_client=PowerMemClient(fake)))
    )

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/lifecycle/run",
        json={"current_day": 90},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["trace_id"].startswith("trace_")
    assert body["act_key"] == "Act 10"
    assert body["data_source"] == "scenario_seed"
    assert body["memory_hits"][0]["content"] == "Masked temporary_context memory"
    assert body["selected_memory_ids"] == []
    assert body["vehicle_state_diff"] == []
    assert body["privacy_report"]["redaction_count"] == 0
    assert body["evidence"]["operations"] == body["operations"]
    assert body["evidence"]["lifecycle"]["trace_id"] == body["trace_id"]
    assert body["lifecycle"]["trace_id"] == body["trace_id"]
    assert body["completed_operations"] == []
    assert body["failed_operation"]["memory_id"] == "temp-1"
    assert body["operations"][0]["result"] == "failed"
    assert all(entry["trace_id"] == body["trace_id"] for entry in body["audit"])
    recent = client.get(
        "/api/scenarios/smart-ev-cockpit/state"
    ).json()["recent_operations"]
    assert recent[-1]["trace_id"] == body["trace_id"]
