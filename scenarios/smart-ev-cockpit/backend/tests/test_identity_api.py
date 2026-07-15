from pathlib import Path

from fastapi.testclient import TestClient

from app.dependencies import AppContainer
from app.domain.memory_models import MemoryMetadata, MemoryRecord
from app.main import create_app
from app.powermem.client import PowerMemClient
from app.services.chat_history_service import ChatHistoryService
from app.services.identity_service import IdentityService


class IdentityApiMemory:
    def __init__(self):
        self.add_calls = []
        self.search_calls = []
        self.get_all_calls = []
        self.records = [
            MemoryRecord(
                memory_id="profile-1",
                content="guest_alex profile prefers quiet assistant wording.",
                metadata=MemoryMetadata(
                    actor_id="driver_primary",
                    seat_position="front_left",
                    memory_kind="person_profile",
                    memory_dimension=["profile"],
                    created_at="2026-07-10T00:00:00Z",
                ),
            )
        ]

    def add(self, content, **kwargs):
        self.add_calls.append({"content": content, **kwargs})
        return {"results": [{"id": "added-identity-pref", "memory": content}]}

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return {"results": []}

    def get_all(self, **kwargs):
        self.get_all_calls.append(kwargs)
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


def _client(tmp_path: Path):
    memory = IdentityApiMemory()
    container = AppContainer(
        powermem_client=PowerMemClient(memory),
        chat_history_service=ChatHistoryService(tmp_path / "chat.sqlite3"),
        identity_service=IdentityService(tmp_path / "identities.sqlite3"),
    )
    return TestClient(create_app(container=container)), memory


def test_identity_api_lists_default_actor_bindings(tmp_path):
    client, _ = _client(tmp_path)

    response = client.get("/api/scenarios/smart-ev-cockpit/identities")

    assert response.status_code == 200
    body = response.json()
    assert [identity["actor_id"] for identity in body["identities"]] == [
        "driver_primary",
        "passenger_front",
        "child_rear_left",
    ]
    assert body["identities"][0]["user_id"] == "driver_primary"


def test_identity_api_updates_actor_user_binding(tmp_path):
    client, _ = _client(tmp_path)

    response = client.put(
        "/api/scenarios/smart-ev-cockpit/identities/driver_primary",
        json={
            "user_id": "guest_alex",
            "display_name": "Alex",
            "profile_note": "Temporary demo driver",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["identity"]["actor_id"] == "driver_primary"
    assert body["identity"]["user_id"] == "guest_alex"
    assert body["identity"]["display_name"] == "Alex"
    assert body["identity"]["profile_note"] == "Temporary demo driver"


def test_identity_api_returns_powermem_profile_for_bound_user(tmp_path):
    client, memory = _client(tmp_path)
    client.put(
        "/api/scenarios/smart-ev-cockpit/identities/driver_primary",
        json={"user_id": "guest_alex", "display_name": "Alex"},
    )

    response = client.get("/api/scenarios/smart-ev-cockpit/profiles/driver_primary")

    assert response.status_code == 200
    body = response.json()
    assert memory.get_all_calls[0]["user_id"] == "guest_alex"
    assert body["profile"]["identity"]["user_id"] == "guest_alex"
    assert body["profile"]["primary_memory"] == (
        "guest_alex profile prefers quiet assistant wording."
    )
    assert body["profile"]["memory_kind_counts"] == {"person_profile": 1}


def test_utter_request_uses_bound_user_id_for_powermem_and_chat_history(tmp_path):
    client, memory = _client(tmp_path)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "act_key": "Act 1",
            "actor_id": "driver_primary",
            "user_id": "guest_alex",
            "seat_position": "front_left",
            "text": "冬天上车一般 26C，座椅加热 2 档。",
            "session_id": "identity-session",
        },
    )
    history = client.get(
        "/api/scenarios/smart-ev-cockpit/chat-history",
        params={
            "session_id": "identity-session",
            "actor_id": "driver_primary",
            "user_id": "guest_alex",
        },
    )

    assert response.status_code == 200
    assert memory.add_calls[0]["user_id"] == "guest_alex"
    assert response.json()["evidence"]["request"]["user_id"] == "guest_alex"
    assert history.status_code == 200
    assert {message["user_id"] for message in history.json()["messages"]} == {
        "guest_alex"
    }


def test_utter_search_uses_bound_user_id_for_powermem_lookup(tmp_path):
    client, memory = _client(tmp_path)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "act_key": "Act 2",
            "actor_id": "driver_primary",
            "user_id": "guest_alex",
            "seat_position": "front_left",
            "text": "I feel cold.",
            "session_id": "identity-search-session",
        },
    )

    assert response.status_code == 200
    assert memory.search_calls[0]["user_id"] == "guest_alex"
