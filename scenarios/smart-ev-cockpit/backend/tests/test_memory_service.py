from app.domain.memory_models import MemoryMetadata, MemoryRecord
from app.powermem.client import PowerMemClient
from app.services.memory_service import MemoryService


def _raw(record: MemoryRecord) -> dict:
    return {
        "id": record.memory_id,
        "memory": record.content,
        "metadata": record.metadata.model_dump(mode="json"),
    }


def _record(
    memory_id: str,
    *,
    actor_id: str = "driver_primary",
    seat_position: str = "front_left",
    memory_kind: str = "cabin_control_preference",
) -> MemoryRecord:
    return MemoryRecord(
        memory_id=memory_id,
        content="driver winter preference target_temp_c=26; seat_heat_level=2",
        metadata=MemoryMetadata(
            actor_id=actor_id,
            seat_position=seat_position,
            memory_kind=memory_kind,
            created_at="2026-07-12T00:00:00Z",
            target_temp_c=26,
            seat_heat_level=2,
        ),
    )


class SearchMissListHitPowerMem:
    def __init__(self, records: list[MemoryRecord]):
        self.records = records
        self.search_calls: list[dict] = []
        self.get_all_calls: list[dict] = []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return {"results": []}

    def get_all(self, **kwargs):
        self.get_all_calls.append(kwargs)
        filters = kwargs.get("filters") or {}
        if set(filters) - {"scenario_id", "vehicle_id"}:
            return {"results": []}
        return {"results": [_raw(record) for record in self.records]}


def test_search_falls_back_to_list_and_filters_metadata_in_application():
    raw_memory = SearchMissListHitPowerMem(
        [
            _record("driver-cabin"),
            _record(
                "passenger-cabin",
                actor_id="passenger_front",
                seat_position="front_right",
            ),
        ]
    )
    service = MemoryService(PowerMemClient(raw_memory))

    records = service.search(
        query="cold cabin preferences and safety policy for driver_primary front_left",
        user_id="driver_primary",
        filters={
            "scenario_id": "smart_ev_cockpit",
            "vehicle_id": "demo_vehicle_001",
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "memory_kind": {
                "in": ["cabin_control_preference", "safety_policy"]
            },
        },
        limit=10,
    )

    assert [record.memory_id for record in records] == ["driver-cabin"]
    assert raw_memory.search_calls[0]["filters"] == {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "actor_id": "driver_primary",
        "seat_position": "front_left",
        "memory_kind": {
            "in": ["cabin_control_preference", "safety_policy"]
        },
    }
    assert raw_memory.search_calls[1]["filters"] == {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
    }
    assert raw_memory.get_all_calls == [
        {
            "filters": {
                "scenario_id": "smart_ev_cockpit",
                "vehicle_id": "demo_vehicle_001",
            },
            "user_id": "driver_primary",
            "limit": 2000,
        }
    ]
