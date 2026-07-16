import pytest

from app.powermem.client import PowerMemClient, PowerMemConnectionError
from app.powermem.queries import build_cold_cabin_query
from app.services.memory_service import MemoryService


def test_build_cold_cabin_query_uses_actor_filters():
    query = build_cold_cabin_query(actor_id="driver_primary", seat_position="front_left")

    assert query.query == "winter cold cabin comfort preference for driver_primary front_left"
    assert query.user_id == "driver_primary"
    assert query.filters["scenario_id"] == "smart_ev_cockpit"
    assert query.filters["memory_kind"] == {
        "in": [
            "cabin_control_preference",
            "emotional_preference",
            "temporary_context",
        ]
    }


def test_memory_service_raises_when_powermem_unavailable():
    client = PowerMemClient(memory=None)
    service = MemoryService(client=client)

    with pytest.raises(PowerMemConnectionError, match="PowerMem is not connected"):
        service.search(query="anything", filters={}, limit=1)
