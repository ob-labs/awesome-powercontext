from datetime import UTC, datetime
from pathlib import Path

from app.domain.memory_models import MemoryMetadata
from app.services.test_data_generator import (
    generate_dataset_id,
    generate_memory_rows,
    read_memory_jsonl,
    write_memory_jsonl,
)


def has_chinese_text(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def test_generate_dataset_id_can_include_generation_time_and_unique_suffix():
    dataset_id = generate_dataset_id(
        count=12,
        seed=7,
        locale="zh",
        generated_at=datetime(2026, 7, 12, 8, 9, 10, tzinfo=UTC),
        unique_suffix="abc123ef",
    )

    assert dataset_id == "smart_ev_cockpit_20260712_080910_12_seed7_zh_abc123ef"


def test_generate_memory_rows_creates_realistic_large_dataset():
    dataset_id = generate_dataset_id(count=1200, seed=42)

    rows = generate_memory_rows(count=1200, seed=42, dataset_id=dataset_id)

    assert len(rows) == 1200
    assert {row.user_id for row in rows} >= {
        "driver_primary",
        "passenger_front",
        "child_rear_left",
    }
    assert {row.metadata["memory_kind"] for row in rows} >= {
        "cabin_control_preference",
        "driving_preference",
        "vehicle_capability",
        "location_episode",
        "media_preference",
        "relationship_event",
        "temporary_context",
        "safety_policy",
    }
    assert {row.metadata["visibility"] for row in rows} >= {
        "public_demo",
        "masked",
        "hidden",
    }
    assert {row.metadata["lifecycle_status"] for row in rows} >= {
        "active",
        "reinforced",
        "decayed",
    }
    assert all(row.dataset_id == dataset_id for row in rows)
    assert all(row.metadata["dataset_id"] == dataset_id for row in rows)
    assert all(row.content for row in rows)
    assert all(row.user_id for row in rows)
    driving_rows = [
        row for row in rows
        if row.metadata["memory_kind"] == "driving_preference"
    ]
    assert driving_rows
    assert all(row.metadata["drive_mode"] == "comfort" for row in driving_rows)
    location_rows = [
        row for row in rows
        if row.metadata["memory_kind"] == "location_episode"
    ]
    assert location_rows
    assert all(row.metadata["region"] in row.content for row in location_rows)
    media_rows = [
        row for row in rows
        if row.metadata["memory_kind"] == "media_preference"
    ]
    assert media_rows
    assert all("media_volume" in row.metadata for row in media_rows)
    assert all("content_category" in row.metadata for row in media_rows)
    child_safety_rows = [
        row for row in rows
        if row.metadata["memory_kind"] == "safety_policy"
        and row.metadata["actor_id"] == "child_rear_left"
    ]
    assert child_safety_rows
    assert all(row.metadata["max_media_volume"] == 16 for row in child_safety_rows)
    relationship_rows = [
        row for row in rows
        if row.metadata["memory_kind"] == "relationship_event"
        and row.metadata["actor_id"] == "driver_primary"
    ]
    assert relationship_rows
    assert all(
        row.metadata["relationship_recommendation"] == "calm_dinner"
        for row in relationship_rows
    )
    assert all(
        row.metadata["recommendation_hint"] == "calm dinner"
        for row in relationship_rows
    )
    capability_rows = [
        row for row in rows
        if row.metadata["memory_kind"] == "vehicle_capability"
    ]
    assert len(capability_rows) == 1
    assert capability_rows[0].metadata["capability_feature"] == "rest_mode"
    assert capability_rows[0].metadata["capability_supported"] is True
    assert (
        capability_rows[0].metadata["capability_source_field"]
        == "masked_vehicle_profile"
    )

    for row in rows:
        MemoryMetadata.model_validate(row.metadata)


def test_fixed_seed_generator_covers_act_required_kinds_reproducibly():
    first = generate_memory_rows(count=20, seed=42)
    second = generate_memory_rows(count=20, seed=42)

    assert first == second
    assert len(first) == 20
    assert {row.metadata["memory_kind"] for row in first} >= {
        "cabin_control_preference",
        "driving_preference",
        "vehicle_capability",
        "location_episode",
        "media_preference",
        "safety_policy",
        "relationship_event",
    }


def test_generate_memory_rows_supports_chinese_locale():
    dataset_id = generate_dataset_id(count=12, seed=7, locale="zh")

    rows = generate_memory_rows(count=12, seed=7, dataset_id=dataset_id, locale="zh")

    assert dataset_id == "smart_ev_cockpit_12_seed7_zh"
    assert len(rows) == 12
    assert all(row.dataset_id == dataset_id for row in rows)
    assert all(row.metadata["dataset_id"] == dataset_id for row in rows)
    assert all(row.metadata["locale"] == "zh" for row in rows)
    assert any(has_chinese_text(row.content) for row in rows)
    assert any("座舱" in row.content for row in rows)
    location_regions = {
        row.metadata["region"]
        for row in rows
        if row.metadata["memory_kind"] == "location_episode"
    }
    assert location_regions
    assert location_regions <= {"虹桥商务区", "浦东滨江", "张江科学城"}


def test_generate_memory_rows_uses_summer_profile_for_generation_date():
    rows = generate_memory_rows(
        count=12,
        seed=7,
        locale="zh",
        generated_at=datetime(2026, 7, 12, 8, 0, tzinfo=UTC),
    )
    cabin_rows = [
        row
        for row in rows
        if row.metadata["memory_kind"] == "cabin_control_preference"
        and "座椅加热" in row.content
    ]

    assert cabin_rows
    assert all(row.metadata["season"] == "summer" for row in cabin_rows)
    assert all(row.metadata["target_temp_c"] in {22, 23, 24} for row in cabin_rows)
    assert all(row.metadata["seat_heat_level"] == 0 for row in cabin_rows)
    assert all("夏季" in row.content for row in cabin_rows)


def test_generate_memory_rows_uses_winter_profile_for_generation_date():
    rows = generate_memory_rows(
        count=12,
        seed=7,
        locale="en",
        generated_at=datetime(2026, 1, 12, 8, 0, tzinfo=UTC),
    )
    cabin_rows = [
        row
        for row in rows
        if row.metadata["memory_kind"] == "cabin_control_preference"
        and "seat heat" in row.content
    ]

    assert cabin_rows
    assert all(row.metadata["season"] == "winter" for row in cabin_rows)
    assert all(row.metadata["target_temp_c"] in {25, 26, 27} for row in cabin_rows)
    assert all(row.metadata["seat_heat_level"] in {1, 2, 3} for row in cabin_rows)
    assert all("winter" in row.content for row in cabin_rows)


def test_generate_memory_rows_uses_actor_user_id_mapping():
    rows = generate_memory_rows(
        count=4,
        seed=7,
        actor_user_ids={"driver_primary": "driver_live_user"},
    )

    driver_rows = [
        row for row in rows
        if row.metadata["actor_id"] == "driver_primary"
    ]
    non_driver_rows = [
        row for row in rows
        if row.metadata["actor_id"] != "driver_primary"
    ]

    assert driver_rows
    assert all(row.user_id == "driver_live_user" for row in driver_rows)
    assert all(row.user_id == row.metadata["actor_id"] for row in non_driver_rows)


def test_generated_memory_jsonl_round_trips(tmp_path: Path):
    dataset_id = generate_dataset_id(count=12, seed=7)
    rows = generate_memory_rows(count=12, seed=7, dataset_id=dataset_id)
    output_path = tmp_path / f"{dataset_id}.jsonl"

    write_memory_jsonl(output_path, rows)
    loaded_rows = read_memory_jsonl(output_path)

    assert loaded_rows == rows
