from pydantic import BaseModel, Field

from app.domain.memory_models import MemoryRecord


class UserIdentity(BaseModel):
    actor_id: str
    seat_position: str
    user_id: str
    display_name: str
    profile_note: str = ""
    updated_at: str


class UpdateUserIdentityRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=80)
    display_name: str | None = Field(default=None, max_length=80)
    profile_note: str | None = Field(default=None, max_length=240)


class UserProfileSummary(BaseModel):
    identity: UserIdentity
    primary_memory: str | None = None
    memory_kind_counts: dict[str, int] = Field(default_factory=dict)
    memories: list[MemoryRecord] = Field(default_factory=list)
