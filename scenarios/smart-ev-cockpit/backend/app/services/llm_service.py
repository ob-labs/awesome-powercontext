import re
from typing import Any

import httpx


class LlmConnectionError(RuntimeError):
    pass


_PERSISTENCE_CLAIM_PATTERNS = {
    "ADD": (
        re.compile(r"(?:已|已经)(?:记住|记下|保存|记录)"),
        re.compile(r"(?:记住|记下|保存|记录)了"),
        re.compile(r"(?:我会|会为您)(?:记住|记下|保存|记录)"),
        re.compile(r"(?:已|已经)将.{0,80}(?:保存|记录|写入)"),
        re.compile(
            r"\b(?:i(?:'ve| have)|we(?:'ve| have))\s+"
            r"(?:saved|remembered|recorded)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bi(?:'ll| will)\s+remember\b", re.IGNORECASE),
    ),
    "UPDATE": (
        re.compile(r"(?:已|已经)(?:更新|修改)"),
        re.compile(r"(?:更新|修改)了"),
        re.compile(r"(?:我会|会为您)(?:更新|修改)"),
        re.compile(r"(?:已|已经)将.{0,80}(?:更新|修改)"),
        re.compile(
            r"\b(?:i(?:'ve| have)|we(?:'ve| have))\s+(?:updated|modified)\b",
            re.IGNORECASE,
        ),
    ),
    "DELETE": (
        re.compile(r"(?:已|已经)(?:删除|移除)"),
        re.compile(r"(?:删除|移除)了"),
        re.compile(r"(?:我会|会为您)(?:删除|移除)"),
        re.compile(r"(?:已|已经)将.{0,80}(?:删除|移除)"),
        re.compile(
            r"\b(?:i(?:'ve| have)|we(?:'ve| have))\s+(?:deleted|removed)\b",
            re.IGNORECASE,
        ),
    ),
}


class OpenAICompatibleLlmClient:
    def __init__(
        self,
        *,
        provider: str,
        model: str,
        base_url: str,
        api_key: str | None,
        timeout_seconds: float = 30.0,
    ):
        self.provider = provider
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def chat(
        self,
        *,
        user_text: str,
        actor_id: str,
        seat_position: str,
        vehicle_state: dict,
        memory_hits: list[dict[str, Any]],
        memory_mutations: list[dict[str, Any]] | None = None,
    ) -> str:
        memory_mutations = memory_mutations or []
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the assistant in a smart EV cockpit demo. Answer the user "
                    "directly in the same language as the user. Use the provided vehicle "
                    "state and PowerMem memory hits when relevant. Do not claim access to "
                    "live internet, live weather, or external tools. If the user asks for "
                    "real-time weather, say that live weather is unavailable and mention "
                    "vehicle sensor readings if useful. Only claim a memory was saved when "
                    "an ADD mutation is present. Only claim a memory was updated when an "
                    "UPDATE mutation is present. Only claim a memory was deleted when a "
                    "DELETE mutation is present. A SEARCH hit or PowerMem connectivity is "
                    "not proof that this turn was saved. Do not describe an ADD, UPDATE, "
                    "or DELETE unless that exact mutation is present. Keep the answer "
                    "concise."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"actor_id: {actor_id}\n"
                    f"seat_position: {seat_position}\n"
                    f"vehicle_state: {vehicle_state}\n"
                    f"powermem_memory_hits: {memory_hits}\n"
                    f"powermem_memory_mutations: {memory_mutations}\n"
                    f"user_utterance: {user_text}"
                ),
            },
        ]
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3,
                    "stream": False,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise LlmConnectionError(f"LLM chat request failed: {exc}") from exc

        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmConnectionError("LLM chat response did not include message content") from exc

        if not isinstance(content, str) or not content.strip():
            raise LlmConnectionError("LLM chat response was empty")
        content = content.strip()
        _validate_persistence_claim(content, memory_mutations)
        return content


def _validate_persistence_claim(
    content: str,
    memory_mutations: list[dict[str, Any]],
) -> None:
    events = {
        str(mutation.get("event", "")).upper() for mutation in memory_mutations
    }
    for event, patterns in _PERSISTENCE_CLAIM_PATTERNS.items():
        if event not in events and any(pattern.search(content) for pattern in patterns):
            raise LlmConnectionError(
                "LLM returned an unsupported memory persistence claim"
            )
