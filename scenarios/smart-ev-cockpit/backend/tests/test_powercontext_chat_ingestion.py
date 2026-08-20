from datetime import UTC, datetime

import pytest

from app.domain.scenario_models import ActRequest
from app.powercontext.client import PowerContextClient, PowerContextResponseError
from app.powercontext.mappers import powercontext_hit_to_record
from app.services.chat_memory_service import ChatMemoryService


class InferencePowerContext:
    def __init__(self, result):
        self.result = result
        self.add_calls = []

    def add(self, messages, user_id=None, metadata=None, infer=False):
        self.add_calls.append(
            {
                "messages": messages,
                "user_id": user_id,
                "metadata": metadata,
                "infer": infer,
            }
        )
        return self.result


def test_infer_memories_accepts_empty_results():
    raw = InferencePowerContext({"results": []})
    client = PowerContextClient(raw)

    mutations = client.infer_memories(
        messages=[{"role": "user", "content": "今天天气如何"}],
        user_id="driver_primary",
        metadata={"memory_kind": "person_profile"},
    )

    assert mutations == []
    assert raw.add_calls == [
        {
            "messages": [{"role": "user", "content": "今天天气如何"}],
            "user_id": "driver_primary",
            "metadata": {"memory_kind": "person_profile"},
            "infer": True,
        }
    ]


def test_infer_memories_preserves_mutation_events():
    raw = InferencePowerContext(
        {
            "results": [
                {"id": "mem_add", "memory": "用户喜欢咖啡", "event": "ADD"},
                {
                    "id": "mem_update",
                    "memory": "用户现在喜欢茶",
                    "previous_memory": "用户喜欢咖啡",
                    "event": "UPDATE",
                },
                {
                    "id": "mem_delete",
                    "memory": "用户不再喝汽水",
                    "event": "DELETE",
                },
            ]
        }
    )

    mutations = PowerContextClient(raw).infer_memories(
        messages=[{"role": "user", "content": "我的偏好变了"}],
        user_id="driver_primary",
        metadata={"memory_kind": "person_profile"},
    )

    assert [mutation.event for mutation in mutations] == ["ADD", "UPDATE", "DELETE"]
    assert [mutation.memory_id for mutation in mutations] == [
        "mem_add",
        "mem_update",
        "mem_delete",
    ]
    assert mutations[1].previous_content == "用户喜欢咖啡"


@pytest.mark.parametrize(
    "result",
    [
        {},
        {"results": "invalid"},
        {"results": [{"memory": "missing id", "event": "ADD"}]},
        {"results": [{"id": "mem_1", "memory": "x", "event": "NONE"}]},
    ],
)
def test_infer_memories_rejects_malformed_results(result):
    with pytest.raises(PowerContextResponseError, match="Source ingestion response"):
        PowerContextClient(InferencePowerContext(result)).infer_memories(
            messages=[{"role": "user", "content": "remember this"}],
            user_id="driver_primary",
            metadata={"memory_kind": "person_profile"},
        )


def test_infer_memories_wraps_sdk_failures():
    class FailingInferencePowerContext:
        def add(self, messages, user_id=None, metadata=None, infer=False):
            raise RuntimeError("OceanBase write failed")

    with pytest.raises(RuntimeError, match="PowerContext Source ingestion failed") as exc:
        PowerContextClient(FailingInferencePowerContext()).infer_memories(
            messages=[{"role": "user", "content": "我喜欢喝咖啡"}],
            user_id="driver_primary",
            metadata={"memory_kind": "person_profile"},
        )

    assert type(exc.value).__name__ == "PowerContextIngestionError"


def test_mapper_hydrates_created_at_from_powercontext_result():
    record = powercontext_hit_to_record(
        {
            "id": "mem_profile",
            "memory": "用户喜欢咖啡",
            "created_at": datetime(2026, 7, 17, 8, 0, tzinfo=UTC),
            "metadata": {
                "scenario_id": "smart_ev_cockpit",
                "vehicle_id": "demo_vehicle_001",
                "actor_id": "driver_primary",
                "seat_position": "front_left",
                "memory_kind": "person_profile",
                "memory_dimension": ["semantic", "profile"],
            },
        }
    )

    assert record.metadata.created_at == "2026-07-17T08:00:00Z"


def test_chat_memory_service_uses_stable_scoped_metadata():
    raw = InferencePowerContext(
        {"results": [{"id": "mem_coffee", "memory": "用户喜欢咖啡", "event": "ADD"}]}
    )
    request = ActRequest(
        act_key="Chat",
        actor_id="driver_primary",
        user_id="guest_alex",
        seat_position="front_left",
        text="我喜欢喝咖啡",
        session_id="demo_session_001",
    )

    result = ChatMemoryService(PowerContextClient(raw)).ingest(
        request=request,
        trace_id="trace_coffee",
    )

    assert raw.add_calls[0] == {
        "messages": [{"role": "user", "content": "我喜欢喝咖啡"}],
        "user_id": "guest_alex",
        "metadata": {
            "scenario_id": "smart_ev_cockpit",
            "vehicle_id": "demo_vehicle_001",
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "memory_kind": "person_profile",
            "memory_dimension": ["semantic", "profile"],
            "memory_layer": "long_term",
            "privacy_level": "public_demo",
            "visibility": "public_demo",
            "source_event_ids": ["demo_session_001:trace_coffee:chat"],
            "lifecycle_status": "active",
            "locale": "zh",
        },
        "infer": True,
    }
    assert [operation.type for operation in result.operations] == ["ADD"]
    assert result.operations[0].memory_ids == ["mem_coffee"]
    assert result.llm_context() == [
        {
            "event": "ADD",
            "memory_id": "mem_coffee",
            "content": "用户喜欢咖啡",
            "previous_content": None,
        }
    ]


@pytest.mark.parametrize(
    "text",
    [
        "我喜欢喝咖啡吗？",
        "我的偏好是什么",
        "今天天气如何",
        "Do I like coffee?",
        "Do you remember that I like coffee?",
        "Did you save this preference?",
    ],
)
def test_chat_memory_service_does_not_ingest_unambiguous_questions(text):
    raw = InferencePowerContext(
        {"results": [{"id": "wrong", "memory": "喜欢喝咖啡", "event": "ADD"}]}
    )
    request = ActRequest(
        act_key="Chat",
        actor_id="driver_primary",
        user_id="driver_primary",
        seat_position="front_left",
        text=text,
        session_id="demo_session_001",
    )

    result = ChatMemoryService(PowerContextClient(raw)).ingest(
        request=request,
        trace_id="trace_question",
    )

    assert result.mutations == []
    assert result.operations == []
    assert raw.add_calls == []


@pytest.mark.parametrize(
    "text",
    [
        "请记住我喜欢无糖咖啡，好吗？",
        "Remember that I like sugar-free coffee.",
    ],
)
def test_chat_memory_service_allows_explicit_remember_request(text):
    raw = InferencePowerContext(
        {
            "results": [
                {"id": "mem_coffee", "memory": "喜欢无糖咖啡", "event": "ADD"}
            ]
        }
    )
    request = ActRequest(
        act_key="Chat",
        actor_id="driver_primary",
        user_id="driver_primary",
        seat_position="front_left",
        text=text,
        session_id="demo_session_001",
    )

    result = ChatMemoryService(PowerContextClient(raw)).ingest(
        request=request,
        trace_id="trace_remember",
    )

    assert [mutation.memory_id for mutation in result.mutations] == ["mem_coffee"]
    assert len(raw.add_calls) == 1
