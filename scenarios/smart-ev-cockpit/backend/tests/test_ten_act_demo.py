from pathlib import Path

from fastapi.testclient import TestClient

from app.data.csv_snapshot_loader import SnapshotResult
from app.dependencies import AppContainer
from app.domain.memory_models import MemoryMetadata, MemoryRecord
from app.main import create_app
from app.powermem.client import PowerMemClient
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


class TenActDemoPowerMem:
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
                lifecycle_status="active",
            ),
            _record(
                "expired-temporary",
                "temporary_context",
                retention_policy="expire_after_valid_until",
                valid_until="2026-03-15",
                lifecycle_status="active",
            ),
        ]
        self.add_calls = []
        self.search_calls = []
        self.get_all_calls = []
        self.update_calls = []
        self.delete_calls = []

    def add(self, content, **kwargs):
        self.add_calls.append({"content": content, **kwargs})
        return {"results": [{"id": "added-preference", "memory": content}]}

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        filters = kwargs["filters"]
        kinds = filters.get("memory_kind")
        allowed = set(kinds.get("in", [])) if isinstance(kinds, dict) else {kinds}
        actor_id = filters.get("actor_id")
        seat_position = filters.get("seat_position")
        rows = [
            record
            for record in self.records
            if record.metadata.memory_kind in allowed
            and (actor_id is None or record.metadata.actor_id == actor_id)
            and (seat_position is None or record.metadata.seat_position == seat_position)
        ]
        return {"results": [_raw(record) for record in rows]}

    def get_all(self, **kwargs):
        self.get_all_calls.append(kwargs)
        filters = kwargs.get("filters") or {}
        kinds = filters.get("memory_kind")
        if isinstance(kinds, dict) and "in" in kinds:
            allowed = set(kinds["in"])
            rows = [
                record
                for record in self.records
                if record.metadata.memory_kind in allowed
            ]
        else:
            rows = list(self.records)
        return {"results": [_raw(record) for record in rows]}

    def update(self, *, memory_id, content, metadata):
        self.update_calls.append(
            {"memory_id": memory_id, "content": content, "metadata": metadata}
        )
        return {"success": True}

    def delete(self, *, memory_id):
        self.delete_calls.append({"memory_id": memory_id})
        return True


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


def _client(tmp_path: Path):
    raw_memory = TenActDemoPowerMem()
    container = AppContainer(
        powermem_client=PowerMemClient(raw_memory),
        chat_history_service=ChatHistoryService(tmp_path / "chat.sqlite3"),
    )
    container.csv_snapshot_loader = SnapshotLoader()
    return TestClient(create_app(container=container)), raw_memory


def _utter(client: TestClient, *, act_key: str, text: str, actor_id: str, seat_position: str):
    return client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "act_key": act_key,
            "actor_id": actor_id,
            "seat_position": seat_position,
            "text": text,
            "session_id": f"ten-act-{act_key}",
        },
    )


def test_ten_act_presenter_sequence_matches_live_contract(tmp_path):
    client, _ = _client(tmp_path)
    responses = []

    act_requests = [
        (
            "Act 1",
            "冬天上车一般 26C，座椅加热 2 档。",
            "driver_primary",
            "front_left",
            "utter",
        ),
        ("Act 2", "有点冷。", "driver_primary", "front_left", "utter"),
        (
            "Act 3",
            "按我上次舒服的设置来。",
            "driver_primary",
            "front_left",
            "utter",
        ),
        (
            "Act 4",
            "这台车支持小憩模式吗？",
            "driver_primary",
            "front_left",
            "utter",
        ),
        (
            "Act 5",
            "带我去上周五那家餐厅。",
            "driver_primary",
            "front_left",
            "utter",
        ),
        (
            "Act 6",
            "放点适合孩子睡觉的内容。",
            "child_rear_left",
            "rear_left",
            "utter",
        ),
        (
            "Act 7",
            "今晚有什么安排建议？",
            "driver_primary",
            "front_left",
            "utter",
        ),
        (
            "Act 8",
            "建议这次出行的驾驶模式。",
            "driver_primary",
            "front_left",
            "utter",
        ),
        ("Act 9", None, "driver_primary", "front_left", "vehicle"),
        ("Act 10", None, "driver_primary", "front_left", "lifecycle"),
    ]

    for act_key, text, actor_id, seat_position, route in act_requests:
        if route == "utter":
            response = _utter(
                client,
                act_key=act_key,
                text=text,
                actor_id=actor_id,
                seat_position=seat_position,
            )
        elif route == "vehicle":
            response = client.post(
                "/api/scenarios/smart-ev-cockpit/events/vehicle",
                json={"soc": 9, "range_km": 42},
            )
        else:
            response = client.post(
                "/api/scenarios/smart-ev-cockpit/lifecycle/run",
                json={"current_day": 90},
            )

        assert response.status_code == 200, response.text
        responses.append(response.json())

    observed_acts = [response["act_key"] for response in responses]
    assert observed_acts == [f"Act {index}" for index in range(1, 11)]
    assert all(response["powermem_connected"] for response in responses)
    assert all(response["evidence"]["operations"] for response in responses)
    assert responses[8]["vehicle_state"]["soc"] < 20
    assert {"UPDATE", "DELETE"} <= {
        operation["type"] for operation in responses[9]["operations"]
    }
