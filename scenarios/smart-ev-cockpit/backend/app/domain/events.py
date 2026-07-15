from typing import Any, Literal

from pydantic import BaseModel, Field

ActorId = Literal["driver_primary", "passenger_front", "child_rear_left"]
SeatPosition = Literal["front_left", "front_right", "rear_left"]


class VehicleProfile(BaseModel):
    vehicle_id: str
    display_name: str
    model_family: str
    platform_version: str
    assistant_version: str
    supported_features: list[str] = Field(default_factory=list)
    unsupported_features: list[str] = Field(default_factory=list)


class CockpitDialogueEvent(BaseModel):
    event_id: str
    occurred_at: str
    session_id: str
    actor_id: ActorId
    seat_position: SeatPosition
    is_child_voice: bool = False
    query: str
    assistant_reply: str | None = None
    commands: dict[str, Any] = Field(default_factory=dict)


class VehicleStateEvent(BaseModel):
    event_id: str
    occurred_at: str
    soc: int
    range_km: int
    inside_temp_c: float
    outside_temp_c: float
    drive_mode: str
    seat_occupied: dict[str, bool] = Field(default_factory=dict)
    hvac: dict[str, Any] = Field(default_factory=dict)
    seat_heat: dict[str, int] = Field(default_factory=dict)
    tire_pressure_alert: bool = False


class MediaEvent(BaseModel):
    event_id: str
    occurred_at: str
    actor_id: ActorId
    media_type: str
    genre: str
    volume: int
    time_of_day: str
    with_child: bool = False


class NavigationEvent(BaseModel):
    event_id: str
    visited_at: str
    actor_id: ActorId
    poi_alias: str
    poi_category: str
    city_area: str
    distance_km: float
    privacy_zone: str


class RelationshipEvent(BaseModel):
    event_id: str
    subject_actor_id: ActorId
    event_type: str
    date_mm_dd: str
    preference_hint: str
    privacy_level: str
