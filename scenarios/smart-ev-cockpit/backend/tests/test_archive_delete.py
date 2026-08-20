import pytest
from fastapi.testclient import TestClient

from app.dependencies import AppContainer
from app.main import create_app
from app.powercontext.client import PowerContextClient
from app.services.memory_service import MemoryService
from tests.fakes import CrudPowerContext, memory_record


class AddResultPowerContext:
    def __init__(self, result):
        self.result = result

    def add(self, content, user_id=None, metadata=None, infer=False):
        return self.result


class MetadataFilterLimitedCrudPowerContext(CrudPowerContext):
    def get_all(
        self,
        *,
        filters: dict | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> dict:
        self.get_all_calls.append(
            {"filters": filters, "user_id": user_id, "limit": limit}
        )
        filters = filters or {}
        if set(filters) - {"scenario_id", "vehicle_id"}:
            return {"results": []}
        return {
            "results": [
                {
                    "id": record.memory_id,
                    "memory": record.content,
                    "metadata": record.metadata.model_dump(mode="json"),
                }
                for record in self.records
            ]
        }


def test_delete_memory_endpoint_calls_powercontext_delete():
    fake = CrudPowerContext(
        [
            memory_record(
                "mem_001",
                metadata_updates={"actor_id": "driver_primary"},
            )
        ],
        delete_result=True,
    )
    app = create_app(
        container=AppContainer(powercontext_client=PowerContextClient(memory=fake))
    )
    client = TestClient(app)

    response = client.delete(
        "/api/scenarios/smart-ev-cockpit/memories/mem_001",
        params={"actor_id": "driver_primary"},
    )

    assert response.status_code == 200
    assert response.json() == {"memory_id": "mem_001", "deleted": True}
    assert fake.delete_calls == [{"memory_id": "mem_001"}]


def test_delete_memory_endpoint_recovers_when_powercontext_metadata_filters_return_empty():
    fake = MetadataFilterLimitedCrudPowerContext(
        [
            memory_record(
                "mem_001",
                metadata_updates={"actor_id": "driver_primary"},
            )
        ],
        delete_result=True,
    )
    app = create_app(
        container=AppContainer(powercontext_client=PowerContextClient(memory=fake))
    )
    client = TestClient(app)

    response = client.delete(
        "/api/scenarios/smart-ev-cockpit/memories/mem_001",
        params={"actor_id": "driver_primary"},
    )

    assert response.status_code == 200
    assert fake.delete_calls == [{"memory_id": "mem_001"}]
    assert fake.get_all_calls[1]["filters"] == {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
    }


def test_delete_memory_requires_actor_id():
    client = TestClient(
        create_app(
            container=AppContainer(
                powercontext_client=PowerContextClient(memory=CrudPowerContext())
            )
        )
    )

    response = client.delete(
        "/api/scenarios/smart-ev-cockpit/memories/mem_001"
    )

    assert response.status_code == 422


def test_delete_memory_rejects_cross_actor_record_without_deleting():
    fake = CrudPowerContext(
        [
            memory_record(
                "mem_001",
                metadata_updates={"actor_id": "passenger_front"},
            )
        ]
    )
    client = TestClient(
        create_app(
            container=AppContainer(powercontext_client=PowerContextClient(memory=fake))
        )
    )

    response = client.delete(
        "/api/scenarios/smart-ev-cockpit/memories/mem_001",
        params={"actor_id": "driver_primary"},
    )

    assert response.status_code == 404
    assert fake.delete_calls == []
    assert fake.get_all_calls[0]["user_id"] == "driver_primary"


def test_delete_memory_returns_503_when_powercontext_is_disconnected():
    client = TestClient(
        create_app(
            container=AppContainer(powercontext_client=PowerContextClient(memory=None))
        ),
        raise_server_exceptions=False,
    )

    response = client.delete(
        "/api/scenarios/smart-ev-cockpit/memories/mem_001",
        params={"actor_id": "driver_primary"},
    )

    assert response.status_code == 503
    assert "PowerContext is not connected" in response.json()["detail"]


def test_archive_preserves_content_when_updating_metadata():
    fake = CrudPowerContext([memory_record("temp-1", content="short context")])
    service = MemoryService(PowerContextClient(fake))

    service.archive(memory_record("temp-1", content="short context"))

    assert fake.update_calls[0]["content"] == "short context"
    assert fake.update_calls[0]["metadata"]["lifecycle_status"] == "archived"


@pytest.mark.parametrize(
    ("delete_result", "expected"),
    [
        ({"deleted": True}, True),
        ({"deleted": False}, False),
        ({"success": True}, True),
        ({"success": False}, False),
    ],
)
def test_delete_normalizes_dictionary_responses(delete_result, expected):
    fake = CrudPowerContext(delete_result=delete_result)

    assert PowerContextClient(fake).delete_memory("mem_001") is expected


def test_list_memories_passes_filters_user_and_limit():
    fake = CrudPowerContext([memory_record("mem_001")])

    rows = PowerContextClient(fake).list_memories(
        filters={"memory_kind": "temporary_context"},
        user_id="driver_primary",
        limit=7,
    )

    assert [row["id"] for row in rows] == ["mem_001"]
    assert fake.get_all_calls == [
        {
            "filters": {"memory_kind": "temporary_context"},
            "user_id": "driver_primary",
            "limit": 7,
        }
    ]


@pytest.mark.parametrize(
    "result",
    [
        {"results": [{"memory": "stored content"}]},
        {"results": [{"id": "mem_001"}]},
    ],
)
def test_add_rejects_rows_missing_required_fields(result):
    client = PowerContextClient(AddResultPowerContext(result))

    with pytest.raises(RuntimeError, match="invalid ADD response"):
        client.add_memory(
            content="requested content",
            metadata=memory_record("input").metadata,
            user_id="driver_primary",
        )


def test_add_preserves_complete_response_compatibility():
    client = PowerContextClient(
        AddResultPowerContext(
            {"results": [{"id": "mem_001", "memory": "stored content"}]}
        )
    )

    records = client.add_memory(
        content="requested content",
        metadata=memory_record("input").metadata,
        user_id="driver_primary",
    )

    assert [(record.memory_id, record.content) for record in records] == [
        ("mem_001", "stored content")
    ]
