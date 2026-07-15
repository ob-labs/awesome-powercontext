from fastapi.testclient import TestClient

from app.dependencies import AppContainer
from app.main import create_app
from app.powermem.client import PowerMemClient
from app.services.chat_history_service import ChatHistoryService


def test_health_returns_live_service_metadata():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "smart-ev-cockpit-backend",
        "scenario_id": "smart_ev_cockpit",
    }


class FakePowerMem:
    def __init__(self):
        self.add_calls = []

    def search(self, query, user_id=None, filters=None, limit=5):
        assert user_id == "driver_primary"
        return {
            "results": [
                {
                    "id": "mem_winter",
                    "memory": "driver_primary prefers 26C and seat heat level 2 in winter.",
                    "metadata": {
                        "scenario_id": "smart_ev_cockpit",
                        "vehicle_id": "demo_vehicle_001",
                        "actor_id": "driver_primary",
                        "seat_position": "front_left",
                        "memory_kind": "cabin_control_preference",
                        "memory_dimension": ["procedural"],
                        "memory_layer": "long_term",
                        "privacy_level": "public_demo",
                        "visibility": "public_demo",
                        "source_event_ids": ["dlg_0001"],
                        "confidence": 0.91,
                        "hit_count": 7,
                        "created_at": "2026-01-08T08:10:00Z",
                        "retention_score": 0.86,
                        "lifecycle_status": "active",
                        "is_sensitive": False,
                    },
                    "score": 0.91,
                }
            ]
        }

    def add(self, content, user_id=None, metadata=None, infer=False):
        self.add_calls.append(
            {
                "content": content,
                "user_id": user_id,
                "metadata": metadata,
                "infer": infer,
            }
        )
        return {"results": [{"id": "mem_usage", "memory": content, "metadata": metadata}]}


class RecordingPowerMem:
    def __init__(self):
        self.add_calls = []
        self.search_calls = []

    def search(self, query, user_id=None, filters=None, limit=5):
        self.search_calls.append(
            {
                "query": query,
                "user_id": user_id,
                "filters": filters,
                "limit": limit,
            }
        )
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
        return {"results": [{"id": "mem_general_chat", "memory": content, "metadata": metadata}]}


class RecordingLlmClient:
    provider = "openai"
    model = "qwen-plus"

    def __init__(self):
        self.chat_calls = []

    def chat(self, *, user_text, actor_id, seat_position, vehicle_state, memory_hits):
        self.chat_calls.append(
            {
                "user_text": user_text,
                "actor_id": actor_id,
                "seat_position": seat_position,
                "vehicle_state": vehicle_state,
                "memory_hits": memory_hits,
            }
        )
        return "我无法获取实时天气，但当前车外温度约 6 C，车内约 22 C。"


def test_utter_returns_trace_evidence_vehicle_diff_and_persists_chat(tmp_path):
    memory = FakePowerMem()
    chat_history = ChatHistoryService(tmp_path / "chat.sqlite3")
    container = AppContainer(
        powermem_client=PowerMemClient(memory=memory),
        chat_history_service=chat_history,
    )
    app = create_app(container=container)
    client = TestClient(app)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "text": "I feel cold.",
            "session_id": "demo_session_001",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["powermem_connected"] is True
    assert body["live_backend"] == "powermem_sdk"
    assert body["trace_id"].startswith("trace_")
    assert body["memory_hits"][0]["memory_id"] == "mem_winter"
    assert {
        "field": "hvac.front_left_target_temp",
        "before": 22,
        "after": 26,
    } in body["vehicle_state_diff"]
    assert body["act_key"] == "Act 2"
    assert body["selected_memory_ids"] == ["mem_winter"]
    assert body["evidence"]["operations"][0]["type"] == "SEARCH"
    stored_messages = chat_history.list_messages(
        session_id="demo_session_001",
        actor_id="driver_primary",
    )
    assert [message.role for message in stored_messages] == ["user", "assistant"]
    assert [message.text for message in stored_messages] == [
        "I feel cold.",
        "I set the driver zone temperature to 26C and set seat heat to level 2.",
    ]
    assert memory.add_calls == []


def test_unknown_unkeyed_utterance_uses_llm_chat_and_persists_turn(tmp_path):
    memory = RecordingPowerMem()
    llm_client = RecordingLlmClient()
    chat_history = ChatHistoryService(tmp_path / "chat.sqlite3")
    container = AppContainer(
        powermem_client=PowerMemClient(memory=memory),
        llm_client=llm_client,
        chat_history_service=chat_history,
    )
    app = create_app(container=container)
    client = TestClient(app)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "text": "今天天气如何",
            "session_id": "demo_session_001",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assistant_reply"] == "我无法获取实时天气，但当前车外温度约 6 C，车内约 22 C。"
    assert body["operations"][0]["type"] == "CHAT"
    assert body["act_key"] == "Chat"
    assert memory.search_calls == [
        {
            "query": "今天天气如何",
            "user_id": "driver_primary",
            "filters": {
                "scenario_id": "smart_ev_cockpit",
                "vehicle_id": "demo_vehicle_001",
                "actor_id": "driver_primary",
                "seat_position": "front_left",
            },
            "limit": 5,
        },
        {
            "query": "今天天气如何",
            "user_id": "driver_primary",
            "filters": {
                "scenario_id": "smart_ev_cockpit",
                "vehicle_id": "demo_vehicle_001",
            },
            "limit": 2000,
        }
    ]
    assert memory.add_calls == []
    assert llm_client.chat_calls == [
        {
            "user_text": "今天天气如何",
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "vehicle_state": body["vehicle_state"],
            "memory_hits": [],
        }
    ]
    stored_messages = chat_history.list_messages(
        session_id="demo_session_001",
        actor_id="driver_primary",
    )
    assert [message.role for message in stored_messages] == ["user", "assistant"]
    assert [message.text for message in stored_messages] == [
        "今天天气如何",
        "我无法获取实时天气，但当前车外温度约 6 C，车内约 22 C。",
    ]


def test_unknown_unkeyed_utterance_uses_memory_chat_when_llm_is_not_configured(
    tmp_path,
):
    memory = FakePowerMem()
    chat_history = ChatHistoryService(tmp_path / "chat.sqlite3")
    container = AppContainer(
        powermem_client=PowerMemClient(memory=memory),
        llm_client=None,
        chat_history_service=chat_history,
    )
    app = create_app(container=container)
    client = TestClient(app)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "text": "我的喜好是什么？",
            "session_id": "demo_session_001",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["act_key"] == "Chat"
    assert body["operations"][0]["type"] == "CHAT"
    assert body["operations"][0]["result"] == "memory_chat_fallback"
    assert body["operations"][1]["type"] == "SEARCH"
    assert body["memory_hits"][0]["memory_id"] == "mem_winter"
    assert body["selected_memory_ids"] == ["mem_winter"]
    assert "我找到 1 条相关记忆" in body["assistant_reply"]
    assert "26C" in body["assistant_reply"]
    stored_messages = chat_history.list_messages(
        session_id="demo_session_001",
        actor_id="driver_primary",
    )
    assert [message.role for message in stored_messages] == ["user", "assistant"]
    assert [message.text for message in stored_messages] == [
        "我的喜好是什么？",
        body["assistant_reply"],
    ]


def test_chat_history_endpoint_filters_messages_by_actor(tmp_path):
    chat_history = ChatHistoryService(tmp_path / "chat.sqlite3")
    chat_history.append_message(
        session_id="demo_session_001",
        actor_id="driver_primary",
        seat_position="front_left",
        role="user",
        text="Driver history",
        trace_id="trace_driver",
        created_at="2026-07-09T10:00:00Z",
    )
    chat_history.append_message(
        session_id="demo_session_001",
        actor_id="passenger_front",
        seat_position="front_right",
        role="user",
        text="Passenger history",
        trace_id="trace_passenger",
        created_at="2026-07-09T10:00:01Z",
    )
    app = create_app(
        container=AppContainer(
            powermem_client=PowerMemClient(memory=RecordingPowerMem()),
            chat_history_service=chat_history,
        )
    )
    client = TestClient(app)

    response = client.get(
        "/api/scenarios/smart-ev-cockpit/chat-history",
        params={"session_id": "demo_session_001", "actor_id": "driver_primary"},
    )

    assert response.status_code == 200
    body = response.json()
    assert [message["text"] for message in body["messages"]] == ["Driver history"]
    assert body["messages"][0]["actor_id"] == "driver_primary"


def test_utter_fails_when_powermem_is_not_connected():
    app = create_app(container=AppContainer(powermem_client=PowerMemClient(memory=None)))
    client = TestClient(app)

    response = client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "text": "I feel cold.",
            "session_id": "demo_session_001",
        },
    )

    assert response.status_code == 503
    assert "PowerMem is not connected" in response.json()["detail"]
