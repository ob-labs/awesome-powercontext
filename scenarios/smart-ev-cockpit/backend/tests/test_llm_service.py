import pytest

from app.services.llm_service import LlmConnectionError, OpenAICompatibleLlmClient


class FakeResponse:
    def __init__(self, content: str):
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": self.content}}]}


def build_client() -> OpenAICompatibleLlmClient:
    return OpenAICompatibleLlmClient(
        provider="openai",
        model="qwen-plus",
        base_url="https://llm.example/v1",
        api_key="test-key",
    )


def test_chat_sends_real_memory_mutations_to_llm(monkeypatch):
    requests = []

    def fake_post(url, **kwargs):
        requests.append({"url": url, **kwargs})
        return FakeResponse("已将咖啡偏好保存到长期记忆。")

    monkeypatch.setattr("app.services.llm_service.httpx.post", fake_post)

    reply = build_client().chat(
        user_text="我喜欢喝咖啡",
        actor_id="driver_primary",
        seat_position="front_left",
        vehicle_state={},
        memory_hits=[],
        memory_mutations=[
            {
                "event": "ADD",
                "memory_id": "mem_coffee",
                "content": "用户喜欢咖啡",
                "previous_content": None,
            }
        ],
    )

    assert reply == "已将咖啡偏好保存到长期记忆。"
    system_message = requests[0]["json"]["messages"][0]["content"]
    user_message = requests[0]["json"]["messages"][1]["content"]
    assert "Only claim a memory was saved when an ADD mutation is present" in system_message
    assert "powercontext_memory_mutations" in user_message
    assert "mem_coffee" in user_message


def test_chat_rejects_unbacked_persistence_claim(monkeypatch):
    monkeypatch.setattr(
        "app.services.llm_service.httpx.post",
        lambda *args, **kwargs: FakeResponse("收到，已记住您喜欢喝咖啡。"),
    )

    with pytest.raises(LlmConnectionError, match="unsupported memory persistence claim"):
        build_client().chat(
            user_text="我喜欢喝咖啡",
            actor_id="driver_primary",
            seat_position="front_left",
            vehicle_state={},
            memory_hits=[],
            memory_mutations=[],
        )


@pytest.mark.parametrize(
    ("reply", "memory_mutations"),
    [
        (
            "已将饮品偏好更新为茶。",
            [{"event": "ADD", "memory_id": "mem_drink", "content": "用户喜欢茶"}],
        ),
        (
            "收到，已记住您喜欢喝茶。",
            [
                {
                    "event": "UPDATE",
                    "memory_id": "mem_drink",
                    "content": "用户喜欢茶",
                }
            ],
        ),
        ("已删除这条饮品偏好。", []),
    ],
)
def test_chat_rejects_claims_backed_by_the_wrong_mutation(
    monkeypatch,
    reply,
    memory_mutations,
):
    monkeypatch.setattr(
        "app.services.llm_service.httpx.post",
        lambda *args, **kwargs: FakeResponse(reply),
    )

    with pytest.raises(LlmConnectionError, match="unsupported memory persistence claim"):
        build_client().chat(
            user_text="我的饮品偏好变了",
            actor_id="driver_primary",
            seat_position="front_left",
            vehicle_state={},
            memory_hits=[],
            memory_mutations=memory_mutations,
        )


@pytest.mark.parametrize(
    ("reply", "memory_mutations"),
    [
        (
            "已记住您喜欢喝咖啡。",
            [{"event": "ADD", "memory_id": "mem_drink", "content": "用户喜欢咖啡"}],
        ),
        (
            "已将饮品偏好更新为茶。",
            [
                {
                    "event": "UPDATE",
                    "memory_id": "mem_drink",
                    "content": "用户喜欢茶",
                }
            ],
        ),
        (
            "已删除这条饮品偏好。",
            [
                {
                    "event": "DELETE",
                    "memory_id": "mem_drink",
                    "content": "用户不再保留饮品偏好",
                }
            ],
        ),
    ],
)
def test_chat_accepts_claims_backed_by_the_matching_mutation(
    monkeypatch,
    reply,
    memory_mutations,
):
    monkeypatch.setattr(
        "app.services.llm_service.httpx.post",
        lambda *args, **kwargs: FakeResponse(reply),
    )

    result = build_client().chat(
        user_text="我的饮品偏好变了",
        actor_id="driver_primary",
        seat_position="front_left",
        vehicle_state={},
        memory_hits=[],
        memory_mutations=memory_mutations,
    )

    assert result == reply
