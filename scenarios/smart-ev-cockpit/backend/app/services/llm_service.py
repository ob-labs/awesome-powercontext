from typing import Any

import httpx


class LlmConnectionError(RuntimeError):
    pass


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
    ) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the assistant in a smart EV cockpit demo. Answer the user "
                    "directly in the same language as the user. Use the provided vehicle "
                    "state and PowerMem memory hits when relevant. Do not claim access to "
                    "live internet, live weather, or external tools. If the user asks for "
                    "real-time weather, say that live weather is unavailable and mention "
                    "vehicle sensor readings if useful. Keep the answer concise."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"actor_id: {actor_id}\n"
                    f"seat_position: {seat_position}\n"
                    f"vehicle_state: {vehicle_state}\n"
                    f"powermem_memory_hits: {memory_hits}\n"
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
        return content.strip()
