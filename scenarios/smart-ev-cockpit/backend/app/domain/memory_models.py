from typing import Literal

from pydantic import BaseModel, Field

MemoryKind = Literal[
    "person_profile",
    "relationship_event",
    "vehicle_capability",
    "cabin_control_preference",
    "media_preference",
    "location_episode",
    "driving_preference",
    "charging_preference",
    "emotional_preference",
    "temporary_context",
    "safety_policy",
]

Visibility = Literal["public_demo", "masked", "hidden", "deleted"]
LifecycleStatus = Literal["active", "reinforced", "decayed", "archived", "deleted"]
MemoryLocale = Literal["en", "zh"]
Season = Literal["spring", "summer", "autumn", "winter"]
DriveMode = Literal["comfort", "eco", "sport"]
EmotionalTone = Literal["calm", "direct", "reassuring"]
ChargingStrategy = Literal["nearest_available", "preferred_network"]
RestrictedControl = Literal["hvac", "seat_heat", "drive_mode"]
MediaCategory = Literal["bedtime_story", "calm_music", "children_audio"]
RelationshipRecommendation = Literal["calm_dinner"]


class MemoryMetadata(BaseModel):
    scenario_id: str = "smart_ev_cockpit"
    vehicle_id: str = "demo_vehicle_001"
    actor_id: str | None = None
    seat_position: str | None = None
    season: Season | None = Field(default=None, exclude_if=lambda value: value is None)
    target_temp_c: float | None = Field(
        default=None, ge=16, le=30, exclude_if=lambda value: value is None
    )
    seat_heat_level: int | None = Field(
        default=None, ge=0, le=3, exclude_if=lambda value: value is None
    )
    drive_mode: DriveMode | None = Field(default=None, exclude_if=lambda value: value is None)
    emotional_tone: EmotionalTone | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    charging_strategy: ChargingStrategy | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    heat_sensitive: bool | None = Field(default=None, exclude_if=lambda value: value is None)
    restricted_controls: list[RestrictedControl] | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    capability_feature: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    capability_supported: bool | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    capability_source_field: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    region: str | None = Field(default=None, exclude_if=lambda value: value is None)
    place_name: str | None = Field(default=None, exclude_if=lambda value: value is None)
    address: str | None = Field(default=None, exclude_if=lambda value: value is None)
    latitude: float | None = Field(default=None, exclude_if=lambda value: value is None)
    longitude: float | None = Field(default=None, exclude_if=lambda value: value is None)
    media_volume: int | None = Field(
        default=None, ge=0, le=100, exclude_if=lambda value: value is None
    )
    content_category: MediaCategory | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    max_media_volume: int | None = Field(
        default=None, ge=0, le=30, exclude_if=lambda value: value is None
    )
    anniversary_date: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    relationship_recommendation: RelationshipRecommendation | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    recommendation_hint: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    session_id: str | None = None
    trace_id: str | None = None
    memory_kind: MemoryKind
    memory_dimension: list[str] = Field(default_factory=list)
    memory_layer: str = "long_term"
    privacy_level: str = "public_demo"
    visibility: Visibility = "public_demo"
    source_event_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.8
    hit_count: int = 0
    created_at: str
    last_accessed_at: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    retention_policy: str = "reinforce_on_hit"
    retention_score: float = 1.0
    lifecycle_status: LifecycleStatus = "active"
    is_sensitive: bool = False
    locale: MemoryLocale = "en"


class MemoryRecord(BaseModel):
    memory_id: str
    content: str
    metadata: MemoryMetadata


class InferredMemoryMutation(BaseModel):
    event: Literal["ADD", "UPDATE", "DELETE"]
    memory_id: str
    content: str
    previous_content: str | None = None


class MemoryOperation(BaseModel):
    type: Literal["SEARCH", "ADD", "UPDATE", "DELETE", "VEHICLE_PATCH", "CHAT"]
    memory_ids: list[str] = Field(default_factory=list)
    query: str | None = None
    filters: dict = Field(default_factory=dict)
    result: str = "ok"


class Recommendation(BaseModel):
    type: str
    title: str
    summary: str
    action_policy: Literal["inform", "suggest", "confirm", "execute"]
    reason_codes: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
