from dataclasses import dataclass

from app.domain.memory_models import InferredMemoryMutation, MemoryOperation
from app.domain.scenario_models import ActRequest
from app.powermem.client import PowerMemClient

_EXPLICIT_MEMORY_REQUEST_PREFIXES = (
    "请记住",
    "请帮我记住",
    "帮我记住",
    "记一下",
    "记下来",
    "别忘了",
    "保存这个",
    "please remember",
    "remember that",
    "please save",
    "save this",
    "please store",
    "store this",
)
_CHINESE_QUESTION_ENDINGS = (
    "吗",
    "嘛",
    "么",
    "呢",
    "什么",
    "如何",
    "怎么",
    "怎么样",
    "哪里",
    "哪儿",
    "是谁",
    "多少",
)
_ENGLISH_QUESTION_PREFIXES = (
    "am ",
    "are ",
    "can ",
    "could ",
    "did ",
    "do ",
    "does ",
    "how ",
    "is ",
    "should ",
    "was ",
    "were ",
    "what ",
    "when ",
    "where ",
    "which ",
    "who ",
    "why ",
    "would ",
)


@dataclass(frozen=True)
class ChatMemoryIngestionResult:
    mutations: list[InferredMemoryMutation]
    operations: list[MemoryOperation]

    def llm_context(self) -> list[dict]:
        return [mutation.model_dump(mode="json") for mutation in self.mutations]


class ChatMemoryService:
    def __init__(self, client: PowerMemClient):
        self.client = client

    def ingest(
        self,
        *,
        request: ActRequest,
        trace_id: str,
    ) -> ChatMemoryIngestionResult:
        if not _should_attempt_ingestion(request.text):
            return ChatMemoryIngestionResult(mutations=[], operations=[])

        mutations = self.client.infer_memories(
            messages=[{"role": "user", "content": request.text}],
            user_id=request.user_id or request.actor_id,
            metadata=_chat_memory_metadata(request, trace_id),
        )
        operations = [
            MemoryOperation(type=mutation.event, memory_ids=[mutation.memory_id])
            for mutation in mutations
        ]
        return ChatMemoryIngestionResult(mutations=mutations, operations=operations)


def _chat_memory_metadata(request: ActRequest, trace_id: str) -> dict:
    return {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "actor_id": request.actor_id,
        "seat_position": request.seat_position,
        "memory_kind": "person_profile",
        "memory_dimension": ["semantic", "profile"],
        "memory_layer": "long_term",
        "privacy_level": "public_demo",
        "visibility": "public_demo",
        "source_event_ids": [f"{request.session_id}:{trace_id}:chat"],
        "lifecycle_status": "active",
        "locale": "zh" if _contains_cjk(request.text) else "en",
    }


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in text)


def _should_attempt_ingestion(text: str) -> bool:
    normalized = text.strip().casefold()
    if not normalized:
        return False
    if normalized.startswith(_EXPLICIT_MEMORY_REQUEST_PREFIXES):
        return True
    if "?" in normalized or "？" in normalized:
        return False
    without_terminal_punctuation = normalized.rstrip("。.!！")
    if without_terminal_punctuation.endswith(_CHINESE_QUESTION_ENDINGS):
        return False
    return not normalized.startswith(_ENGLISH_QUESTION_PREFIXES)
