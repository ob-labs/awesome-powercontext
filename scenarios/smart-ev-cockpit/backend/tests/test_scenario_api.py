from fastapi.testclient import TestClient

from app.dependencies import AppContainer
from app.main import create_app
from app.powermem.client import PowerMemClient
from app.services.chat_history_service import ChatHistoryService
from app.services.llm_service import LlmConnectionError


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
        if infer:
            return {"results": []}
        return {"results": [{"id": "mem_usage", "memory": content, "metadata": metadata}]}


class RecordingPowerMem:
    def __init__(self, infer_results=None):
        self.add_calls = []
        self.search_calls = []
        self.infer_results = infer_results if infer_results is not None else []

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

    def add(self, messages, user_id=None, metadata=None, infer=False):
        self.add_calls.append(
            {
                "messages": messages,
                "user_id": user_id,
                "metadata": metadata,
                "infer": infer,
            }
        )
        return {"results": self.infer_results}


class RecordingLlmClient:
    provider = "openai"
    model = "qwen-plus"

    def __init__(
        self,
        reply="我无法获取实时天气，但当前车外温度约 6 C，车内约 22 C。",
    ):
        self.reply = reply
        self.chat_calls = []

    def chat(
        self,
        *,
        user_text,
        actor_id,
        seat_position,
        vehicle_state,
        memory_hits,
        memory_mutations=None,
    ):
        self.chat_calls.append(
            {
                "user_text": user_text,
                "actor_id": actor_id,
                "seat_position": seat_position,
                "vehicle_state": vehicle_state,
                "memory_hits": memory_hits,
                "memory_mutations": memory_mutations,
            }
        )
        return self.reply


def build_chat_api(tmp_path, memory, llm_client=None):
    history = ChatHistoryService(tmp_path / "chat.sqlite3")
    llm = llm_client or RecordingLlmClient()
    client = TestClient(
        create_app(
            container=AppContainer(
                powermem_client=PowerMemClient(memory),
                llm_client=llm,
                chat_history_service=history,
            )
        )
    )
    return client, history, llm


def post_free_form_chat(client, text):
    return client.post(
        "/api/scenarios/smart-ev-cockpit/utter",
        json={
            "actor_id": "driver_primary",
            "user_id": "driver_primary",
            "seat_position": "front_left",
            "text": text,
            "session_id": "demo_session_001",
        },
    )


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
    assert [operation["type"] for operation in body["operations"]] == [
        "CHAT",
        "SEARCH",
    ]
    assert body["act_key"] == "Chat"
    assert body["data_source"] == "powermem_sdk+llm"
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
            "memory_mutations": [],
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


def test_free_form_preference_runs_real_powermem_add(tmp_path):
    memory = RecordingPowerMem(
        [{"id": "mem_coffee", "memory": "用户喜欢咖啡", "event": "ADD"}]
    )
    llm = RecordingLlmClient(reply="已将咖啡偏好保存到长期记忆。")
    client, history, llm = build_chat_api(tmp_path, memory, llm)

    response = post_free_form_chat(client, "我喜欢喝咖啡")

    assert response.status_code == 200
    body = response.json()
    assert [operation["type"] for operation in body["operations"]] == [
        "CHAT",
        "ADD",
        "SEARCH",
    ]
    assert body["operations"][1]["memory_ids"] == ["mem_coffee"]
    assert body["data_source"] == "powermem_sdk+llm"
    assert memory.add_calls[0]["infer"] is True
    assert llm.chat_calls[0]["memory_mutations"][0]["memory_id"] == "mem_coffee"
    assert len(history.list_messages(session_id="demo_session_001")) == 2


def test_changed_preference_preserves_powermem_update(tmp_path):
    memory = RecordingPowerMem(
        [
            {
                "id": "mem_drink",
                "memory": "用户现在喜欢喝茶",
                "previous_memory": "用户喜欢喝咖啡",
                "event": "UPDATE",
            }
        ]
    )
    llm = RecordingLlmClient(reply="已将饮品偏好更新为茶。")
    client, _, llm = build_chat_api(tmp_path, memory, llm)

    response = post_free_form_chat(client, "我现在改喝茶了")

    assert response.status_code == 200
    body = response.json()
    assert [operation["type"] for operation in body["operations"]] == [
        "CHAT",
        "UPDATE",
        "SEARCH",
    ]
    assert body["operations"][1]["memory_ids"] == ["mem_drink"]
    mutation = llm.chat_calls[0]["memory_mutations"][0]
    assert mutation == {
        "event": "UPDATE",
        "memory_id": "mem_drink",
        "content": "用户现在喜欢喝茶",
        "previous_content": "用户喜欢喝咖啡",
    }


def test_chat_returns_503_when_powermem_ingestion_fails(tmp_path):
    class FailingInferencePowerMem(RecordingPowerMem):
        def add(self, messages, user_id=None, metadata=None, infer=False):
            self.add_calls.append(
                {
                    "messages": messages,
                    "user_id": user_id,
                    "metadata": metadata,
                    "infer": infer,
                }
            )
            raise RuntimeError("OceanBase write failed")

    memory = FailingInferencePowerMem()
    client, history, llm = build_chat_api(tmp_path, memory)

    response = post_free_form_chat(client, "我喜欢喝咖啡")

    assert response.status_code == 503
    assert "PowerMem intelligent ingestion failed" in response.json()["detail"]
    assert history.list_messages(session_id="demo_session_001") == []
    assert llm.chat_calls == []


def test_chat_reports_successful_mutation_when_llm_generation_fails(tmp_path):
    class FailingLlmClient(RecordingLlmClient):
        def chat(self, **kwargs):
            self.chat_calls.append(kwargs)
            raise LlmConnectionError("gateway timeout")

    memory = RecordingPowerMem(
        [{"id": "mem_coffee", "memory": "用户喜欢咖啡", "event": "ADD"}]
    )
    client, history, llm = build_chat_api(tmp_path, memory, FailingLlmClient())

    response = post_free_form_chat(client, "我喜欢喝咖啡")

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert "PowerMem mutation succeeded" in detail
    assert "ADD:mem_coffee" in detail
    assert "gateway timeout" in detail
    assert history.list_messages(session_id="demo_session_001") == []
    assert len(llm.chat_calls) == 1


def test_chat_ingests_scrubbed_text_instead_of_raw_sensitive_input(tmp_path):
    memory = RecordingPowerMem()
    client, _, _ = build_chat_api(tmp_path, memory)

    response = post_free_form_chat(client, "我喜欢咖啡，电话13812345678")

    assert response.status_code == 200
    ingested = memory.add_calls[0]["messages"][0]["content"]
    assert ingested == "我喜欢咖啡，电话[REDACTED_PHONE]"
    assert "13812345678" not in ingested


def test_exact_coffee_question_passes_recent_chat_memory_to_llm(tmp_path):
    seed_metadata = {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "actor_id": "driver_primary",
        "seat_position": "front_left",
        "memory_kind": "cabin_control_preference",
        "created_at": "2026-08-01T00:00:00Z",
        "confidence": 0.99,
        "source_event_ids": ["gen_comfort_001"],
        "_fusion_info": {"fts_rank": None, "vector_rank": 2},
    }
    coffee_metadata = {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "actor_id": "driver_primary",
        "seat_position": "front_left",
        "memory_kind": "person_profile",
        "created_at": "2026-07-17T09:11:56Z",
        "confidence": 0.8,
        "source_event_ids": ["demo_session_001:trace_coffee:chat"],
        "_fusion_info": {"fts_rank": 1, "vector_rank": 1},
    }

    class ChatRecallPowerMem(RecordingPowerMem):
        def search(self, query, user_id=None, filters=None, limit=5):
            self.search_calls.append(
                {
                    "query": query,
                    "user_id": user_id,
                    "filters": filters,
                    "limit": limit,
                }
            )
            if set(filters or {}) - {"scenario_id", "vehicle_id"}:
                return {"results": []}
            return {
                "results": [
                    {
                        "id": "seed-cabin",
                        "memory": "summer cabin temperature preference",
                        "metadata": seed_metadata,
                    },
                    {
                        "id": "mem_coffee",
                        "memory": "喜欢喝咖啡",
                        "metadata": coffee_metadata,
                    },
                ]
            }

    memory = ChatRecallPowerMem()
    llm = RecordingLlmClient(reply="是的，您喜欢喝咖啡。")
    client, _, llm = build_chat_api(tmp_path, memory, llm)

    response = post_free_form_chat(client, "我喜欢喝咖啡吗")

    assert response.status_code == 200
    body = response.json()
    assert body["selected_memory_ids"][0] == "mem_coffee"
    search = next(
        operation
        for operation in body["operations"]
        if operation["type"] == "SEARCH"
    )
    assert search["memory_ids"][0] == "mem_coffee"
    assert memory.add_calls == []
    assert llm.chat_calls[0]["memory_hits"][0]["memory_id"] == "mem_coffee"


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
