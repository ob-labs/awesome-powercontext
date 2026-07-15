from typing import Literal

from pydantic import BaseModel, Field

from app.domain.memory_models import MemoryOperation, MemoryRecord, Recommendation

ActKey = Literal[
    "Act 1",
    "Act 2",
    "Act 3",
    "Act 4",
    "Act 5",
    "Act 6",
    "Act 7",
    "Act 8",
    "Act 9",
    "Act 10",
    "Chat",
]


class VehicleContext(BaseModel):
    hvac_target_temp_c: float = Field(ge=16, le=30)


class ActRequest(BaseModel):
    act_key: ActKey | None = None
    actor_id: str
    user_id: str | None = None
    seat_position: str
    text: str
    session_id: str
    vehicle_context: VehicleContext | None = None


class ActResult(BaseModel):
    act_key: ActKey
    assistant_reply: str
    memory_hits: list[MemoryRecord] = Field(default_factory=list)
    selected_memory_ids: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    vehicle_patch: dict = Field(default_factory=dict)
    recommendations: list[Recommendation] = Field(default_factory=list)
    operations: list[MemoryOperation] = Field(default_factory=list)
    data_source: str = "scenario_seed"


class ScenarioClock(BaseModel):
    current_day: int = Field(default=1, ge=1, le=90)
    text: str | None = None
