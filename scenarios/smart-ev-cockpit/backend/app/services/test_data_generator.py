import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from random import Random
from typing import Any

from app.domain.memory_models import MemoryLocale, MemoryMetadata, Season

ACTORS = {
    "driver_primary": "front_left",
    "passenger_front": "front_right",
    "child_rear_left": "rear_left",
}


@dataclass(frozen=True)
class GeneratedMemoryRow:
    dataset_id: str
    content: str
    user_id: str
    metadata: dict[str, Any]


def generate_dataset_id(
    count: int,
    seed: int,
    locale: MemoryLocale = "en",
    *,
    generated_at: datetime | None = None,
    unique_suffix: str | None = None,
) -> str:
    parts = ["smart_ev_cockpit"]
    if generated_at is not None:
        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(tzinfo=UTC)
        generated_at = generated_at.astimezone(UTC)
        parts.append(generated_at.strftime("%Y%m%d_%H%M%S"))
    parts.extend([str(count), f"seed{seed}"])
    if locale == "zh":
        parts.append("zh")
    if unique_suffix:
        suffix_segment = _dataset_id_segment(unique_suffix)
        if suffix_segment:
            parts.append(suffix_segment)
    return "_".join(parts)


def generate_memory_rows(
    count: int = 1200,
    seed: int = 42,
    dataset_id: str | None = None,
    locale: MemoryLocale = "en",
    actor_user_ids: dict[str, str] | None = None,
    generated_at: datetime | None = None,
) -> list[GeneratedMemoryRow]:
    if count < 1:
        raise ValueError("count must be greater than zero")

    rng = Random(seed)
    generation_time = _generation_time(generated_at)
    season = season_for_date(generation_time)
    resolved_dataset_id = dataset_id or generate_dataset_id(
        count=count,
        seed=seed,
        locale=locale,
        generated_at=generation_time if generated_at is not None else None,
    )
    templates = _memory_templates(locale)
    choices = _localized_choices(locale)
    rows: list[GeneratedMemoryRow] = []

    for index in range(count):
        template = templates[index % len(templates)]
        actor_id = _actor_for_template(template, index)
        seat_position = ACTORS[actor_id]
        occurred_at = generation_time + timedelta(
            days=index % 45,
            minutes=(index * 17) % 720,
        )
        cabin_values = _seasonal_cabin_values(rng, season)
        confidence = round(rng.uniform(0.66, 0.96), 2)
        hit_count = rng.randint(0, 18)
        retention_score = round(rng.uniform(0.35, 0.98), 2)
        template_values = {
            "actor_id": actor_id,
            "actor_label": choices["actor_labels"][actor_id],
            "seat_position": seat_position,
            "seat_label": choices["seat_labels"][seat_position],
            "season_label": choices["season_labels"][season],
            "temp": cabin_values["temp"],
            "seat_heat": cabin_values["seat_heat"],
            "volume": rng.choice([14, 18, 22, 28, 34]),
            "city_area": rng.choice(choices["city_areas"]),
            "day_type": rng.choice(choices["day_types"]),
        }
        metadata = {
            "scenario_id": "smart_ev_cockpit",
            "vehicle_id": "demo_vehicle_001",
            "actor_id": actor_id,
            "seat_position": seat_position,
            "memory_kind": template["memory_kind"],
            "memory_dimension": template["memory_dimension"],
            "memory_layer": template.get("memory_layer", "long_term"),
            "privacy_level": template["privacy_level"],
            "visibility": template["visibility"],
            "source_event_ids": [f"gen_{template['event_prefix']}_{index + 1:06d}"],
            "confidence": confidence,
            "hit_count": hit_count,
            "created_at": occurred_at.isoformat().replace("+00:00", "Z"),
            "last_accessed_at": None,
            "valid_from": None,
            "valid_until": _valid_until(template, occurred_at),
            "retention_policy": template.get("retention_policy", "reinforce_on_hit"),
            "retention_score": retention_score,
            "lifecycle_status": _lifecycle_status(index),
            "is_sensitive": template["visibility"] != "public_demo",
            "dataset_id": resolved_dataset_id,
            "locale": locale,
        }
        if template["memory_kind"] == "location_episode":
            metadata["region"] = template_values["city_area"]
        if template["memory_kind"] == "driving_preference":
            metadata["drive_mode"] = "comfort"
        if template.get("seasonal_cabin_control"):
            metadata["season"] = season
            metadata["target_temp_c"] = template_values["temp"]
            metadata["seat_heat_level"] = template_values["seat_heat"]
        if template["memory_kind"] == "media_preference":
            metadata["media_volume"] = template_values["volume"]
            metadata["content_category"] = (
                "bedtime_story"
                if template.get("event_prefix") == "child_media"
                else "calm_music"
            )
        if template["memory_kind"] == "relationship_event":
            metadata["relationship_recommendation"] = "calm_dinner"
            metadata["recommendation_hint"] = "calm dinner"
        if (
            template["memory_kind"] == "safety_policy"
            and actor_id == "child_rear_left"
        ):
            metadata["max_media_volume"] = 16
        MemoryMetadata.model_validate(metadata)
        rows.append(
            GeneratedMemoryRow(
                dataset_id=resolved_dataset_id,
                content=template["content"].format(**template_values),
                user_id=_user_id_for_actor(actor_id, actor_user_ids),
                metadata=metadata,
            )
        )

    return rows


def season_for_date(value: datetime) -> Season:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    month = value.month
    if 3 <= month <= 5:
        return "spring"
    if 6 <= month <= 8:
        return "summer"
    if 9 <= month <= 11:
        return "autumn"
    return "winter"


def write_memory_jsonl(path: Path, rows: list[GeneratedMemoryRow]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(
                json.dumps(
                    {
                        "dataset_id": row.dataset_id,
                        "content": row.content,
                        "user_id": row.user_id,
                        "metadata": row.metadata,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            file.write("\n")
    return path


def read_memory_jsonl(path: Path) -> list[GeneratedMemoryRow]:
    rows: list[GeneratedMemoryRow] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            rows.append(
                GeneratedMemoryRow(
                    dataset_id=payload["dataset_id"],
                    content=payload["content"],
                    user_id=payload["user_id"],
                    metadata=payload["metadata"],
                )
            )
    return rows


def _dataset_id_segment(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value).strip("_")


def _generation_time(generated_at: datetime | None) -> datetime:
    if generated_at is None:
        return datetime(2026, 1, 8, 7, 30, tzinfo=UTC)
    if generated_at.tzinfo is None:
        return generated_at.replace(tzinfo=UTC)
    return generated_at.astimezone(UTC)


def _seasonal_cabin_values(rng: Random, season: Season) -> dict[str, int]:
    profiles = {
        "spring": {"temps": [23, 24, 25], "seat_heat": [0, 1]},
        "summer": {"temps": [22, 23, 24], "seat_heat": [0]},
        "autumn": {"temps": [23, 24, 25], "seat_heat": [0, 1]},
        "winter": {"temps": [25, 26, 27], "seat_heat": [1, 2, 3]},
    }
    profile = profiles[season]
    return {
        "temp": rng.choice(profile["temps"]),
        "seat_heat": rng.choice(profile["seat_heat"]),
    }


def _actor_for_template(template: dict[str, Any], index: int) -> str:
    actors = template.get("actors")
    if actors:
        return actors[index % len(actors)]
    return list(ACTORS)[index % len(ACTORS)]


def _user_id_for_actor(actor_id: str, actor_user_ids: dict[str, str] | None) -> str:
    if actor_user_ids is None:
        return actor_id
    return actor_user_ids.get(actor_id, actor_id)


def _valid_until(template: dict[str, Any], occurred_at: datetime) -> str | None:
    if template["memory_kind"] != "temporary_context":
        return None
    return (occurred_at + timedelta(days=7)).isoformat().replace("+00:00", "Z")


def _lifecycle_status(index: int) -> str:
    statuses = ["active", "reinforced", "decayed"]
    return statuses[index % len(statuses)]


def _localized_choices(locale: MemoryLocale) -> dict[str, Any]:
    if locale == "zh":
        return {
            "actor_labels": {
                "driver_primary": "驾驶员",
                "passenger_front": "前排乘客",
                "child_rear_left": "后排儿童",
            },
            "seat_labels": {
                "front_left": "主驾座位",
                "front_right": "副驾座位",
                "rear_left": "左后排座位",
            },
            "city_areas": ["虹桥商务区", "浦东滨江", "张江科学城"],
            "day_types": ["工作日", "雨天", "周末", "夜间"],
            "season_labels": {
                "spring": "春季",
                "summer": "夏季",
                "autumn": "秋季",
                "winter": "冬季",
            },
        }
    return {
        "actor_labels": {
            "driver_primary": "driver",
            "passenger_front": "front passenger",
            "child_rear_left": "rear child passenger",
        },
        "seat_labels": {
            "front_left": "front-left seat",
            "front_right": "front-right seat",
            "rear_left": "rear-left seat",
        },
        "city_areas": [
            "Hongqiao Business District",
            "Pudong Riverside",
            "Zhangjiang Science City",
        ],
        "day_types": ["weekday", "rainy", "weekend", "late-night"],
        "season_labels": {
            "spring": "spring",
            "summer": "summer",
            "autumn": "autumn",
            "winter": "winter",
        },
    }


def _memory_templates(locale: MemoryLocale) -> list[dict[str, Any]]:
    if locale == "zh":
        return [
            {
                "memory_kind": "cabin_control_preference",
                "memory_dimension": ["procedural"],
                "privacy_level": "public_demo",
                "visibility": "public_demo",
                "event_prefix": "cabin",
                "seasonal_cabin_control": True,
                "content": (
                    "{actor_label}在{season_label}{day_type}座舱启动时偏好{temp}°C，"
                    "座椅加热保持{seat_heat}档。"
                ),
                "actors": ["driver_primary", "passenger_front"],
            },
            {
                "memory_kind": "cabin_control_preference",
                "memory_dimension": ["procedural", "environmental"],
                "privacy_level": "public_demo",
                "visibility": "public_demo",
                "event_prefix": "comfort",
                "content": (
                    "{actor_label}在{seat_label}偏好低风噪、暖脚部出风和柔和氛围灯。"
                ),
            },
            {
                "memory_kind": "driving_preference",
                "memory_dimension": ["procedural"],
                "privacy_level": "public_demo",
                "visibility": "public_demo",
                "event_prefix": "drive",
                "content": (
                    "{actor_label}在{day_type}城区路线上偏好舒适驾驶模式和更强动能回收。"
                ),
                "actors": ["driver_primary"],
            },
            {
                "memory_kind": "vehicle_capability",
                "memory_dimension": ["capability"],
                "privacy_level": "public_demo",
                "visibility": "public_demo",
                "event_prefix": "capability",
                "content": "车辆的小憩模式能力由脱敏车型配置确认。",
                "actors": ["driver_primary"],
            },
            {
                "memory_kind": "location_episode",
                "memory_dimension": ["episodic", "spatial"],
                "privacy_level": "masked",
                "visibility": "masked",
                "event_prefix": "nav",
                "content": "{actor_label}下班后经常请求前往{city_area}的脱敏目的地。",
                "actors": ["driver_primary", "passenger_front"],
            },
            {
                "memory_kind": "media_preference",
                "memory_dimension": ["preference"],
                "privacy_level": "public_demo",
                "visibility": "public_demo",
                "event_prefix": "media",
                "content": "{actor_label}在{day_type}行程中偏好音量{volume}和舒缓歌单。",
            },
            {
                "memory_kind": "media_preference",
                "memory_dimension": ["preference", "family"],
                "privacy_level": "masked",
                "visibility": "masked",
                "event_prefix": "child_media",
                "content": "后排儿童对音量{volume}的安静睡前故事反馈更好。",
                "actors": ["child_rear_left"],
            },
            {
                "memory_kind": "relationship_event",
                "memory_dimension": ["episodic", "relationship"],
                "privacy_level": "masked",
                "visibility": "masked",
                "event_prefix": "relationship",
                "content": (
                    "{actor_label}在纪念日行程中有家庭偏好提示："
                    "播放平静音乐并降低座舱亮度。"
                ),
                "actors": ["driver_primary", "passenger_front"],
            },
            {
                "memory_kind": "temporary_context",
                "memory_dimension": ["working"],
                "memory_layer": "short_term",
                "privacy_level": "public_demo",
                "visibility": "public_demo",
                "retention_policy": "expire_after_valid_until",
                "event_prefix": "temporary",
                "content": "{actor_label}本周{day_type}计划在{city_area}临时接人。",
            },
            {
                "memory_kind": "safety_policy",
                "memory_dimension": ["policy"],
                "privacy_level": "hidden",
                "visibility": "hidden",
                "event_prefix": "safety",
                "content": (
                    "当检测到{actor_label}是儿童语音时，限制支付、导航变更和高音量媒体。"
                ),
                "actors": ["child_rear_left"],
            },
            {
                "memory_kind": "safety_policy",
                "memory_dimension": ["policy", "vehicle_state"],
                "privacy_level": "public_demo",
                "visibility": "public_demo",
                "event_prefix": "vehicle_safety",
                "content": "{actor_label}长途{day_type}出行前应收到低电量路线建议。",
                "actors": ["driver_primary"],
            },
            {
                "memory_kind": "emotional_preference",
                "memory_dimension": ["affective"],
                "privacy_level": "masked",
                "visibility": "masked",
                "event_prefix": "emotion",
                "content": "{actor_label}在夜间座舱互动中偏好更平静的助手措辞和更少打扰。",
            },
            {
                "memory_kind": "person_profile",
                "memory_dimension": ["profile"],
                "privacy_level": "hidden",
                "visibility": "hidden",
                "event_prefix": "profile",
                "content": "{actor_label}档案将{seat_label}与个性化座舱和媒体默认值关联。",
            },
        ]

    return [
        {
            "memory_kind": "cabin_control_preference",
            "memory_dimension": ["procedural"],
            "privacy_level": "public_demo",
            "visibility": "public_demo",
            "event_prefix": "cabin",
            "seasonal_cabin_control": True,
            "content": (
                "{actor_id} prefers {temp}C and seat heat level {seat_heat} "
                "during {season_label} {day_type} cabin starts."
            ),
            "actors": ["driver_primary", "passenger_front"],
        },
        {
            "memory_kind": "cabin_control_preference",
            "memory_dimension": ["procedural", "environmental"],
            "privacy_level": "public_demo",
            "visibility": "public_demo",
            "event_prefix": "comfort",
            "content": (
                "{actor_id} likes low fan noise, warm footwell airflow, "
                "and calm lighting from {seat_position}."
            ),
        },
        {
            "memory_kind": "driving_preference",
            "memory_dimension": ["procedural"],
            "privacy_level": "public_demo",
            "visibility": "public_demo",
            "event_prefix": "drive",
            "content": (
                "{actor_id} prefers comfort mode in city traffic and stronger "
                "regenerative braking on {day_type} routes."
            ),
            "actors": ["driver_primary"],
        },
        {
            "memory_kind": "vehicle_capability",
            "memory_dimension": ["capability"],
            "privacy_level": "public_demo",
            "visibility": "public_demo",
            "event_prefix": "capability",
            "content": "Rest mode capability is verified against the masked vehicle profile.",
            "actors": ["driver_primary"],
        },
        {
            "memory_kind": "location_episode",
            "memory_dimension": ["episodic", "spatial"],
            "privacy_level": "masked",
            "visibility": "masked",
            "event_prefix": "nav",
            "content": (
                "{actor_id} often asks for a masked destination in the {city_area} "
                "after work."
            ),
            "actors": ["driver_primary", "passenger_front"],
        },
        {
            "memory_kind": "media_preference",
            "memory_dimension": ["preference"],
            "privacy_level": "public_demo",
            "visibility": "public_demo",
            "event_prefix": "media",
            "content": (
                "{actor_id} prefers audio volume {volume} with relaxed playlists "
                "during {day_type} drives."
            ),
        },
        {
            "memory_kind": "media_preference",
            "memory_dimension": ["preference", "family"],
            "privacy_level": "masked",
            "visibility": "masked",
            "event_prefix": "child_media",
            "content": "{actor_id} responds well to quiet bedtime stories at volume {volume}.",
            "actors": ["child_rear_left"],
        },
        {
            "memory_kind": "relationship_event",
            "memory_dimension": ["episodic", "relationship"],
            "privacy_level": "masked",
            "visibility": "masked",
            "event_prefix": "relationship",
            "content": (
                "{actor_id} has a family preference hint for calm music and low "
                "cabin brightness on anniversary trips."
            ),
            "actors": ["driver_primary", "passenger_front"],
        },
        {
            "memory_kind": "temporary_context",
            "memory_dimension": ["working"],
            "memory_layer": "short_term",
            "privacy_level": "public_demo",
            "visibility": "public_demo",
            "retention_policy": "expire_after_valid_until",
            "event_prefix": "temporary",
            "content": (
                "{actor_id} temporarily plans a pickup in the {city_area} "
                "during this week's {day_type} schedule."
            ),
        },
        {
            "memory_kind": "safety_policy",
            "memory_dimension": ["policy"],
            "privacy_level": "hidden",
            "visibility": "hidden",
            "event_prefix": "safety",
            "content": (
                "When {actor_id} is detected as a child voice, restrict payment, "
                "navigation changes, and high volume media."
            ),
            "actors": ["child_rear_left"],
        },
        {
            "memory_kind": "safety_policy",
            "memory_dimension": ["policy", "vehicle_state"],
            "privacy_level": "public_demo",
            "visibility": "public_demo",
            "event_prefix": "vehicle_safety",
            "content": (
                "{actor_id} should receive low battery routing suggestions before "
                "long {day_type} trips."
            ),
            "actors": ["driver_primary"],
        },
        {
            "memory_kind": "emotional_preference",
            "memory_dimension": ["affective"],
            "privacy_level": "masked",
            "visibility": "masked",
            "event_prefix": "emotion",
            "content": (
                "{actor_id} prefers calmer assistant wording and fewer prompts "
                "during late evening cabin interactions."
            ),
        },
        {
            "memory_kind": "person_profile",
            "memory_dimension": ["profile"],
            "privacy_level": "hidden",
            "visibility": "hidden",
            "event_prefix": "profile",
            "content": (
                "{actor_id} profile links seat position {seat_position} with "
                "personalized cabin and media defaults."
            ),
        },
    ]
