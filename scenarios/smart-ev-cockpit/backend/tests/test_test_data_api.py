import re
from pathlib import Path
from threading import Event
from time import sleep

from fastapi.testclient import TestClient

from app.dependencies import AppContainer
from app.main import create_app
from app.powercontext.client import PowerContextClient
from app.services.identity_service import IdentityService
from app.services.test_data_service import TestDataService


class RecordingMemory:
    def __init__(self, existing_rows=None):
        self.add_calls = []
        self.delete_calls = []
        self.get_all_calls = []
        self.existing_rows = (
            existing_rows if existing_rows is not None else [{"id": "mem_001"}]
        )

    def add(self, content, user_id=None, metadata=None, infer=True):
        self.add_calls.append(
            {
                "content": content,
                "user_id": user_id,
                "metadata": metadata,
                "infer": infer,
            }
        )
        return {"results": [{"id": "mem_001"}]}

    def get_all(self, user_id=None, filters=None, limit=100, offset=0):
        self.get_all_calls.append(
            {"user_id": user_id, "filters": filters, "limit": limit}
        )
        return {"results": self.existing_rows[offset:offset + limit]}

    def delete(self, memory_id=None):
        self.delete_calls.append(memory_id)
        self.existing_rows = [
            row for row in self.existing_rows if str(row.get("id")) != str(memory_id)
        ]
        return True


class BlockingMemory(RecordingMemory):
    def __init__(self, existing_rows=None):
        super().__init__(existing_rows=existing_rows)
        self.started = Event()
        self.release = Event()

    def add(self, content, user_id=None, metadata=None, infer=True):
        self.started.set()
        if not self.release.wait(timeout=2):
            raise TimeoutError("blocked import was not released")
        return super().add(content, user_id=user_id, metadata=metadata, infer=infer)


def build_client(tmp_path: Path, memory=None) -> TestClient:
    container = AppContainer(
        powercontext_client=PowerContextClient(memory=memory),
        test_data_service=TestDataService(data_root=tmp_path),
        identity_service=IdentityService(tmp_path / "identities.sqlite3"),
    )
    return TestClient(create_app(container=container))


def assert_generated_dataset_id(
    dataset_id: str,
    count: int,
    seed: int,
    locale: str = "en",
) -> None:
    locale_segment = "_zh" if locale == "zh" else ""
    assert re.fullmatch(
        rf"smart_ev_cockpit_\d{{8}}_\d{{6}}_{count}_seed{seed}{locale_segment}_[0-9a-f]{{8}}",
        dataset_id,
    )


def test_generate_test_data_endpoint_creates_dataset(tmp_path: Path):
    client = build_client(tmp_path, memory=RecordingMemory())

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/test-data/generate",
        json={"count": 1000, "seed": 42},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "generated"
    assert body["generated_count"] == 1000
    assert_generated_dataset_id(body["dataset_id"], count=1000, seed=42)


def test_generate_test_data_endpoint_defaults_to_1200_rows(tmp_path: Path):
    client = build_client(tmp_path, memory=RecordingMemory())

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/test-data/generate",
        json={"seed": 42},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["generated_count"] == 1200
    assert_generated_dataset_id(body["dataset_id"], count=1200, seed=42)


def test_generate_test_data_endpoint_creates_chinese_dataset(tmp_path: Path):
    client = build_client(tmp_path, memory=RecordingMemory())

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/test-data/generate",
        json={"count": 4, "seed": 99, "locale": "zh"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "generated"
    assert body["locale"] == "zh"
    assert_generated_dataset_id(body["dataset_id"], count=4, seed=99, locale="zh")
    assert Path(body["dataset_path"]).read_text(encoding="utf-8").find("座舱") >= 0


def test_status_endpoint_returns_latest_dataset(tmp_path: Path):
    client = build_client(tmp_path, memory=RecordingMemory())
    client.post(
        "/api/scenarios/smart-ev-cockpit/test-data/generate",
        json={"count": 1000, "seed": 9},
    )

    response = client.get("/api/scenarios/smart-ev-cockpit/test-data/status")

    assert response.status_code == 200
    assert_generated_dataset_id(response.json()["dataset_id"], count=1000, seed=9)


def test_import_test_data_endpoint_starts_background_import_with_progress(
    tmp_path: Path,
):
    memory = BlockingMemory(existing_rows=[])
    client = build_client(tmp_path, memory=memory)
    generated = client.post(
        "/api/scenarios/smart-ev-cockpit/test-data/generate",
        json={"count": 4, "seed": 2},
    ).json()

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/test-data/import",
        json={
            "dataset_id": generated["dataset_id"],
            "apply": True,
            "max_workers": 2,
        },
    )

    assert response.status_code == 200
    assert response.json()["state"] == "importing"
    assert memory.started.wait(timeout=1)

    progress = client.get("/api/scenarios/smart-ev-cockpit/test-data/status").json()
    assert progress["state"] == "importing"
    assert progress["generated_count"] == 4

    memory.release.set()
    for _ in range(30):
        finished = client.get("/api/scenarios/smart-ev-cockpit/test-data/status").json()
        if finished["state"] == "imported":
            break
        sleep(0.05)

    assert finished["state"] == "imported"
    assert finished["imported_count"] == 4
    assert len(memory.add_calls) == 4


def test_import_test_data_request_defaults_to_three_workers():
    from app.api.routes_test_data import ImportTestDataRequest

    payload = ImportTestDataRequest(dataset_id="dataset_001", apply=True)

    assert payload.max_workers == 3


def test_generate_and_import_test_data_use_current_identity_bindings(
    tmp_path: Path,
):
    memory = RecordingMemory(existing_rows=[])
    client = build_client(tmp_path, memory=memory)
    identity_response = client.put(
        "/api/scenarios/smart-ev-cockpit/identities/driver_primary",
        json={
            "user_id": "driver_live_user",
            "display_name": "测试驾驶员",
        },
    )
    assert identity_response.status_code == 200

    generated = client.post(
        "/api/scenarios/smart-ev-cockpit/test-data/generate",
        json={"count": 4, "seed": 2, "locale": "zh"},
    ).json()

    dataset_text = Path(generated["dataset_path"]).read_text(encoding="utf-8")
    assert '"user_id":"driver_live_user"' in dataset_text

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/test-data/import",
        json={"dataset_id": generated["dataset_id"], "apply": True},
    )

    assert response.status_code == 200
    for _ in range(30):
        finished = client.get("/api/scenarios/smart-ev-cockpit/test-data/status").json()
        if finished["state"] == "imported":
            break
        sleep(0.05)

    driver_calls = [
        call for call in memory.add_calls
        if call["metadata"]["actor_id"] == "driver_primary"
    ]
    assert driver_calls
    assert all(call["user_id"] == "driver_live_user" for call in driver_calls)


def test_import_test_data_endpoint_skips_duplicate_dataset(tmp_path: Path):
    memory = RecordingMemory(existing_rows=[{"id": "existing_001"}])
    client = build_client(tmp_path, memory=memory)
    generated = client.post(
        "/api/scenarios/smart-ev-cockpit/test-data/generate",
        json={"count": 4, "seed": 22},
    ).json()

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/test-data/import",
        json={"dataset_id": generated["dataset_id"], "apply": True},
    )

    assert response.status_code == 200
    assert response.json()["state"] == "imported"
    assert response.json()["imported_count"] == 1
    assert response.json()["skipped_count"] == 4
    assert memory.add_calls == []
    assert memory.get_all_calls == [
        {
            "user_id": None,
            "filters": {"dataset_id": generated["dataset_id"]},
            "limit": 10000,
        }
    ]


def test_delete_test_dataset_endpoint_deletes_from_powercontext(tmp_path: Path):
    memory = RecordingMemory()
    client = build_client(tmp_path, memory=memory)
    generated = client.post(
        "/api/scenarios/smart-ev-cockpit/test-data/generate",
        json={"count": 2, "seed": 3},
    ).json()

    response = client.request(
        "DELETE",
        f"/api/scenarios/smart-ev-cockpit/test-data/{generated['dataset_id']}",
        json={"apply": True},
    )

    assert response.status_code == 200
    assert response.json()["deleted_count"] == 1
    assert memory.delete_calls == ["mem_001"]


def test_clear_all_test_data_endpoint_deletes_entire_powercontext_collection(
    tmp_path: Path,
):
    memory = RecordingMemory(
        existing_rows=[{"id": "scenario_memory"}, {"id": "other_project_memory"}]
    )
    client = build_client(tmp_path, memory=memory)

    response = client.request(
        "DELETE",
        "/api/scenarios/smart-ev-cockpit/test-data/all",
        json={"apply": True},
    )

    assert response.status_code == 200
    assert response.json()["state"] == "deleted"
    assert response.json()["dataset_id"] is None
    assert response.json()["deleted_count"] == 2
    assert memory.delete_calls == ["scenario_memory", "other_project_memory"]
    assert memory.get_all_calls == [
        {"user_id": None, "filters": None, "limit": 1000},
        {"user_id": None, "filters": None, "limit": 1000},
    ]


def test_import_requires_connected_powercontext(tmp_path: Path):
    client = build_client(tmp_path, memory=None)
    generated = client.post(
        "/api/scenarios/smart-ev-cockpit/test-data/generate",
        json={"count": 2, "seed": 3},
    ).json()

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/test-data/import",
        json={"dataset_id": generated["dataset_id"], "apply": True},
    )

    assert response.status_code == 503
    assert "PowerContext is not connected" in response.json()["detail"]
