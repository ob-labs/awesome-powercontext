from typing import Literal

from pydantic import BaseModel

ChatRole = Literal["user", "assistant"]


class ChatMessageRecord(BaseModel):
    id: str
    session_id: str
    actor_id: str
    user_id: str
    seat_position: str
    role: ChatRole
    text: str
    trace_id: str | None = None
    created_at: str
