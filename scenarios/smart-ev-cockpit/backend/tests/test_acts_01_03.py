from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.domain.memory_models import MemoryMetadata
from app.domain.scenario_models import ActRequest
from app.powermem.client import PowerMemClient
from app.services.acts.act_01_profile import handle as handle_act_01
from app.services.acts.act_02_multi_actor import handle as handle_act_02
from app.services.acts.act_03_routine import handle as handle_act_03
from app.services.acts.base import ActContext


class StubMemory:
    def __init__(self, *, hits=None):
        self.hits = list(hits or [])
        self.add_calls = []
        self.search_calls = []

    def add(self, content, **kwargs):
        self.add_calls.append({"content": content, **kwargs})
        return {"results": [{"id": "mem_added_01", "memory": content}]}

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return {"results": self.hits}


class MetadataFilterLimitedMemory(StubMemory):
    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        filters = kwargs["filters"]
        if set(filters) - {"scenario_id", "vehicle_id"}:
            return {"results": []}
        return {"results": self.hits}


class SearchThenListMemory(StubMemory):
    def __init__(self, *, search_hits=None, list_hits=None):
        super().__init__(hits=search_hits)
        self.list_hits = list(list_hits or [])
        self.get_all_calls = []

    def get_all(self, **kwargs):
        self.get_all_calls.append(kwargs)
        return {"results": self.list_hits}


def context_for(*, act_key, actor_id, seat_position, text, memory=None):
    raw_memory = memory or StubMemory()
    request = ActRequest(
        act_key=act_key,
        actor_id=actor_id,
        seat_position=seat_position,
        text=text,
        session_id="session_test",
    )
    container = SimpleNamespace(powermem_client=PowerMemClient(raw_memory))
    return ActContext(request=request, container=container), raw_memory


def raw_hit(
    memory_id,
    *,
    actor_id,
    seat_position,
    memory_kind,
    content,
    **structured,
):
    return {
        "id": memory_id,
        "memory": content,
        "metadata": {
            "actor_id": actor_id,
            "seat_position": seat_position,
            "memory_kind": memory_kind,
            "created_at": "2026-07-10T00:00:00Z",
            **structured,
        },
    }


def test_memory_metadata_retains_act_01_03_structured_fields():
    metadata = MemoryMetadata(
        actor_id="driver_primary",
        seat_position="front_left",
        memory_kind="cabin_control_preference",
        created_at="2026-07-10T00:00:00Z",
        season="winter",
        target_temp_c=26,
        seat_heat_level=2,
        drive_mode="comfort",
        heat_sensitive=False,
        restricted_controls=["seat_heat"],
    )

    assert metadata.model_dump(mode="json") == {
        **metadata.model_dump(
            mode="json",
            exclude={
                "season",
                "target_temp_c",
                "seat_heat_level",
                "drive_mode",
                "heat_sensitive",
                "restricted_controls",
            },
        ),
        "season": "winter",
        "target_temp_c": 26.0,
        "seat_heat_level": 2,
        "drive_mode": "comfort",
        "heat_sensitive": False,
        "restricted_controls": ["seat_heat"],
    }


@pytest.mark.parametrize(
    "invalid_field",
    [
        {"season": "monsoon"},
        {"drive_mode": "track"},
        {"restricted_controls": ["payment"]},
    ],
)
def test_memory_metadata_rejects_non_whitelisted_act_values(invalid_field):
    with pytest.raises(ValidationError):
        MemoryMetadata(
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="cabin_control_preference",
            created_at="2026-07-10T00:00:00Z",
            **invalid_field,
        )


@pytest.mark.parametrize(
    ("text", "expected_temp", "expected_heat", "expected_season"),
    [
        ("我冬天上车一般 26C，座椅加热 2 档。", 26, 2, "winter"),
        ("Usually set 25C and seat heat level 1 in winter.", 25, 1, "winter"),
        ("夏天车内设为 16°C，座椅加热 0 档。", 16, 0, "summer"),
        ("Set temperature to 30 C and seat heat level 3 in summer.", 30, 3, "summer"),
    ],
)
def test_act_01_parses_scripted_forms_and_adds_structured_memory(
    text, expected_temp, expected_heat, expected_season
):
    context, memory = context_for(
        act_key="Act 1",
        actor_id="driver_primary",
        seat_position="front_left",
        text=text,
    )

    result = handle_act_01(context)

    assert result.vehicle_patch == {
        "hvac": {"front_left_target_temp": expected_temp},
        "seat_heat": {"front_left": expected_heat},
    }
    assert result.reason_codes == ["cabin_preference_saved"]
    assert result.operations[0].type == "ADD"
    assert result.operations[0].memory_ids == ["mem_added_01"]
    assert len(memory.add_calls) == 1
    call = memory.add_calls[0]
    assert call["user_id"] == "driver_primary"
    assert call["infer"] is False
    assert call["metadata"]["memory_kind"] == "cabin_control_preference"
    assert call["metadata"]["actor_id"] == "driver_primary"
    assert call["metadata"]["seat_position"] == "front_left"
    assert call["metadata"]["season"] == expected_season
    assert call["metadata"]["target_temp_c"] == expected_temp
    assert call["metadata"]["seat_heat_level"] == expected_heat
    assert call["metadata"]["source_event_ids"] == [
        "session_test:act_01:cabin_control_preference"
    ]
    assert call["metadata"]["created_at"] != "2026-01-01T00:00:00Z"
    assert call["metadata"]["created_at"].endswith("Z")
    assert "User:" not in call["content"]
    assert "Assistant:" not in call["content"]
    assert f"target_temp_c={expected_temp}" in call["content"]


@pytest.mark.parametrize(
    "text",
    [
        "冬天设为 15C，座椅加热 2 档。",
        "冬天设为 31C，座椅加热 2 档。",
        "Set 22C and seat heat level 4 in winter.",
        "Set 22C in winter.",
    ],
)
def test_act_01_rejects_invalid_or_incomplete_ranges_without_writing(text):
    context, memory = context_for(
        act_key="Act 1",
        actor_id="driver_primary",
        seat_position="front_left",
        text=text,
    )

    result = handle_act_01(context)

    assert result.vehicle_patch == {}
    assert result.operations == []
    assert result.reason_codes == ["invalid_cabin_preference"]
    assert memory.add_calls == []


def test_act_01_replies_in_chinese_for_chinese_preference():
    context, _ = context_for(
        act_key="Act 1",
        actor_id="driver_primary",
        seat_position="front_left",
        text="我冬天上车一般 26C，座椅加热 2 档。",
    )

    result = handle_act_01(context)

    assert result.assistant_reply == "已保存并应用你的座舱偏好。"


@pytest.mark.parametrize(
    ("actor_id", "seat_position", "hits", "expected_patch", "expected_ids"),
    [
        (
            "driver_primary",
            "front_left",
            [
                raw_hit(
                    "driver_cabin",
                    actor_id="driver_primary",
                    seat_position="front_left",
                    memory_kind="cabin_control_preference",
                    content="Driver winter cabin preference.",
                    target_temp_c=27,
                    seat_heat_level=3,
                    season="winter",
                )
            ],
            {
                "hvac": {"front_left_target_temp": 27},
                "seat_heat": {"front_left": 3},
            },
            ["driver_cabin"],
        ),
        (
            "passenger_front",
            "front_right",
            [
                raw_hit(
                    "passenger_cabin",
                    actor_id="passenger_front",
                    seat_position="front_right",
                    memory_kind="cabin_control_preference",
                    content="Passenger is heat sensitive.",
                    target_temp_c=23,
                    seat_heat_level=2,
                    heat_sensitive=True,
                )
            ],
            {
                "hvac": {"front_right_target_temp": 23},
                "seat_heat": {"front_right": 0},
            },
            ["passenger_cabin"],
        ),
        (
            "child_rear_left",
            "rear_left",
            [
                raw_hit(
                    "child_cabin",
                    actor_id="child_rear_left",
                    seat_position="rear_left",
                    memory_kind="cabin_control_preference",
                    content="Child rear cabin preference.",
                    target_temp_c=24,
                    seat_heat_level=2,
                ),
                raw_hit(
                    "child_policy",
                    actor_id="child_rear_left",
                    seat_position="rear_left",
                    memory_kind="safety_policy",
                    content="Child must not control seat heat.",
                    restricted_controls=["seat_heat"],
                ),
            ],
            {"hvac": {"rear_left_target_temp": 24}},
            ["child_cabin", "child_policy"],
        ),
    ],
)
def test_act_02_uses_isolated_hit_driven_values_for_each_occupant(
    actor_id, seat_position, hits, expected_patch, expected_ids
):
    memory = StubMemory(hits=hits)
    context, _ = context_for(
        act_key="Act 2",
        actor_id=actor_id,
        seat_position=seat_position,
        text="I feel cold.",
        memory=memory,
    )

    result = handle_act_02(context)

    assert memory.search_calls == [
        {
            "query": f"cold cabin preferences and safety policy for {actor_id} {seat_position}",
            "user_id": actor_id,
            "filters": {
                "scenario_id": "smart_ev_cockpit",
                "vehicle_id": "demo_vehicle_001",
                "actor_id": actor_id,
                "seat_position": seat_position,
                "memory_kind": {
                    "in": ["cabin_control_preference", "safety_policy"]
                },
            },
            "limit": 10,
        }
    ]
    assert result.vehicle_patch == expected_patch
    assert result.selected_memory_ids == expected_ids
    assert set(result.selected_memory_ids) <= {
        memory.memory_id for memory in result.memory_hits
    }
    assert result.operations[0].type == "SEARCH"


def test_act_02_no_applicable_memory_returns_explicit_no_match():
    memory = StubMemory(
        hits=[
            raw_hit(
                "other_actor",
                actor_id="passenger_front",
                seat_position="front_right",
                memory_kind="cabin_control_preference",
                content="Other occupant preference.",
                target_temp_c=29,
                seat_heat_level=3,
            )
        ]
    )
    context, _ = context_for(
        act_key="Act 2",
        actor_id="driver_primary",
        seat_position="front_left",
        text="有点冷。",
        memory=memory,
    )

    result = handle_act_02(context)

    assert result.vehicle_patch == {}
    assert result.selected_memory_ids == []
    assert result.reason_codes == ["no_applicable_memory"]
    assert result.assistant_reply == "没有找到适用的座舱偏好。"


def test_act_02_replies_in_chinese_for_chinese_cabin_request():
    memory = StubMemory(
        hits=[
            raw_hit(
                "driver_cabin",
                actor_id="driver_primary",
                seat_position="front_left",
                memory_kind="cabin_control_preference",
                content="Driver winter cabin preference.",
                target_temp_c=26,
                seat_heat_level=2,
                season="winter",
            )
        ]
    )
    context, _ = context_for(
        act_key="Act 2",
        actor_id="driver_primary",
        seat_position="front_left",
        text="我觉得有点冷。",
        memory=memory,
    )

    result = handle_act_02(context)

    assert result.assistant_reply == "已将主驾区域温度调到 26C，座椅加热调到 2 档。"


def test_act_02_recovers_when_powermem_does_not_support_metadata_filters():
    memory = MetadataFilterLimitedMemory(
        hits=[
            raw_hit(
                "driver_cabin",
                actor_id="driver_primary",
                seat_position="front_left",
                memory_kind="cabin_control_preference",
                content="Driver winter cabin preference.",
                target_temp_c=26,
                seat_heat_level=2,
                season="winter",
            ),
            raw_hit(
                "passenger_cabin",
                actor_id="passenger_front",
                seat_position="front_right",
                memory_kind="cabin_control_preference",
                content="Passenger winter cabin preference.",
                target_temp_c=28,
                seat_heat_level=3,
                season="winter",
            ),
        ]
    )
    context, _ = context_for(
        act_key="Act 2",
        actor_id="driver_primary",
        seat_position="front_left",
        text="我有点冷。",
        memory=memory,
    )

    result = handle_act_02(context)

    assert result.assistant_reply == "已将主驾区域温度调到 26C，座椅加热调到 2 档。"
    assert result.vehicle_patch == {
        "hvac": {"front_left_target_temp": 26},
        "seat_heat": {"front_left": 2},
    }
    assert result.selected_memory_ids == ["driver_cabin"]
    assert memory.search_calls[1]["filters"] == {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
    }


def test_act_02_is_deterministic_over_identical_hits():
    hits = [
        raw_hit(
            "stable_cabin",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="cabin_control_preference",
            content="Stable preference.",
            target_temp_c=26,
            seat_heat_level=2,
        )
    ]
    first_context, _ = context_for(
        act_key="Act 2",
        actor_id="driver_primary",
        seat_position="front_left",
        text="I feel cold.",
        memory=StubMemory(hits=hits),
    )
    second_context, _ = context_for(
        act_key="Act 2",
        actor_id="driver_primary",
        seat_position="front_left",
        text="I feel cold.",
        memory=StubMemory(hits=hits),
    )

    assert handle_act_02(first_context) == handle_act_02(second_context)


def test_act_02_skips_empty_hits_and_combines_contributing_records():
    hits = [
        raw_hit(
            "empty_high_confidence",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="cabin_control_preference",
            content="No supported cabin values.",
            confidence=0.99,
        ),
        raw_hit(
            "temperature_source",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="cabin_control_preference",
            content="Structured temperature.",
            target_temp_c=27,
            confidence=0.9,
        ),
        raw_hit(
            "heat_source",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="cabin_control_preference",
            content="Structured seat heat.",
            seat_heat_level=3,
            confidence=0.8,
        ),
    ]
    context, _ = context_for(
        act_key="Act 2",
        actor_id="driver_primary",
        seat_position="front_left",
        text="I feel cold.",
        memory=StubMemory(hits=hits),
    )

    result = handle_act_02(context)

    assert result.vehicle_patch == {
        "hvac": {"front_left_target_temp": 27},
        "seat_heat": {"front_left": 3},
    }
    assert result.selected_memory_ids == ["temperature_source", "heat_source"]


def test_act_02_is_order_independent_with_confidence_then_id_priority():
    hits = [
        raw_hit(
            "z_temperature_lower",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="cabin_control_preference",
            content="Lower priority temperature.",
            target_temp_c=22,
            confidence=0.9,
        ),
        raw_hit(
            "a_temperature_preferred",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="cabin_control_preference",
            content="Higher priority temperature.",
            target_temp_c=26,
            confidence=0.9,
        ),
        raw_hit(
            "seat_heat_source",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="cabin_control_preference",
            content="Seat heat source.",
            seat_heat_level=2,
            confidence=0.8,
        ),
    ]

    results = []
    for ordered_hits in (hits, list(reversed(hits))):
        context, _ = context_for(
            act_key="Act 2",
            actor_id="driver_primary",
            seat_position="front_left",
            text="I feel cold.",
            memory=StubMemory(hits=ordered_hits),
        )
        results.append(handle_act_02(context))

    assert results[0].vehicle_patch == {
        "hvac": {"front_left_target_temp": 26},
        "seat_heat": {"front_left": 2},
    }
    assert results[0].selected_memory_ids == [
        "a_temperature_preferred",
        "seat_heat_source",
    ]
    assert results[0].vehicle_patch == results[1].vehicle_patch
    assert results[0].selected_memory_ids == results[1].selected_memory_ids
    assert results[0].reason_codes == results[1].reason_codes


def test_act_02_prefers_newer_memory_when_fallback_list_contains_recent_update():
    old_preference = raw_hit(
        "a_old_cabin",
        actor_id="driver_primary",
        seat_position="front_left",
        memory_kind="cabin_control_preference",
        content="Old winter cabin preference.",
        target_temp_c=24,
        seat_heat_level=1,
        confidence=1.0,
        created_at="2026-01-01T00:00:00Z",
    )
    new_preference = raw_hit(
        "z_new_cabin",
        actor_id="driver_primary",
        seat_position="front_left",
        memory_kind="cabin_control_preference",
        content="New winter cabin preference.",
        target_temp_c=27,
        seat_heat_level=3,
        confidence=1.0,
        created_at="2026-07-12T00:00:00Z",
    )
    context, memory = context_for(
        act_key="Act 2",
        actor_id="driver_primary",
        seat_position="front_left",
        text="我有点冷。",
        memory=SearchThenListMemory(
            search_hits=[old_preference],
            list_hits=[old_preference, new_preference],
        ),
    )

    result = handle_act_02(context)

    assert result.vehicle_patch == {
        "hvac": {"front_left_target_temp": 27},
        "seat_heat": {"front_left": 3},
    }
    assert result.selected_memory_ids == ["z_new_cabin"]
    assert memory.get_all_calls[0]["filters"] == {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
    }


def test_act_02_legacy_safety_text_only_uses_supported_control_whitelist():
    hits = [
        raw_hit(
            "child_cabin",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="cabin_control_preference",
            content="Child cabin controls.",
            target_temp_c=24,
            seat_heat_level=2,
        ),
        raw_hit(
            "unsupported_policy",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="safety_policy",
            content="Restrict payment, navigation changes, and high volume media.",
            confidence=0.99,
        ),
        raw_hit(
            "seat_policy",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="safety_policy",
            content="Child must not control seat heat.",
            confidence=0.8,
        ),
    ]
    context, _ = context_for(
        act_key="Act 2",
        actor_id="child_rear_left",
        seat_position="rear_left",
        text="I feel cold.",
        memory=StubMemory(hits=hits),
    )

    result = handle_act_02(context)

    assert result.vehicle_patch == {"hvac": {"rear_left_target_temp": 24}}
    assert result.selected_memory_ids == ["child_cabin", "seat_policy"]


def test_act_03_composes_complete_cabin_and_driving_routine():
    hits = [
        raw_hit(
            "routine_cabin",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="cabin_control_preference",
            content="Complete cabin routine.",
            target_temp_c=25,
            seat_heat_level=1,
        ),
        raw_hit(
            "routine_drive",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="driving_preference",
            content="Complete driving routine.",
            drive_mode="eco",
        ),
    ]
    memory = StubMemory(hits=hits)
    context, _ = context_for(
        act_key="Act 3",
        actor_id="driver_primary",
        seat_position="front_left",
        text="Use my previous comfort setup.",
        memory=memory,
    )

    result = handle_act_03(context)

    assert memory.search_calls == [
        {
            "query": (
                "previous cabin and driving routine for driver_primary front_left"
            ),
            "user_id": "driver_primary",
            "filters": {
                "scenario_id": "smart_ev_cockpit",
                "vehicle_id": "demo_vehicle_001",
                "actor_id": "driver_primary",
                "seat_position": "front_left",
                "memory_kind": {
                    "in": ["cabin_control_preference", "driving_preference"]
                },
            },
            "limit": 10,
        }
    ]
    assert result.vehicle_patch == {
        "hvac": {"front_left_target_temp": 25},
        "seat_heat": {"front_left": 1},
        "drive_mode": "eco",
    }
    assert result.selected_memory_ids == ["routine_cabin", "routine_drive"]
    assert result.reason_codes == ["complete_routine"]
    assert set(result.selected_memory_ids) <= {
        memory.memory_id for memory in result.memory_hits
    }


@pytest.mark.parametrize(
    ("hits", "expected_patch", "expected_ids"),
    [
        (
            [
                raw_hit(
                    "partial_cabin",
                    actor_id="driver_primary",
                    seat_position="front_left",
                    memory_kind="cabin_control_preference",
                    content="Cabin-only routine.",
                    target_temp_c=24,
                    seat_heat_level=2,
                )
            ],
            {
                "hvac": {"front_left_target_temp": 24},
                "seat_heat": {"front_left": 2},
            },
            ["partial_cabin"],
        ),
        (
            [
                raw_hit(
                    "partial_drive",
                    actor_id="driver_primary",
                    seat_position="front_left",
                    memory_kind="driving_preference",
                    content="Drive-only routine.",
                    drive_mode="sport",
                )
            ],
            {"drive_mode": "sport"},
            ["partial_drive"],
        ),
    ],
)
def test_act_03_applies_only_available_data_without_defaults(
    hits, expected_patch, expected_ids
):
    context, _ = context_for(
        act_key="Act 3",
        actor_id="driver_primary",
        seat_position="front_left",
        text="按我上次舒服的设置来。",
        memory=StubMemory(hits=hits),
    )

    result = handle_act_03(context)

    assert result.vehicle_patch == expected_patch
    assert result.selected_memory_ids == expected_ids
    assert result.reason_codes == ["partial_routine"]


def test_act_03_is_deterministic_and_ignores_noncontributing_records():
    hits = [
        raw_hit(
            "usable_drive",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="driving_preference",
            content="Structured drive mode.",
            drive_mode="comfort",
        ),
        raw_hit(
            "empty_cabin",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="cabin_control_preference",
            content="No actionable structured values.",
        ),
        raw_hit(
            "wrong_actor",
            actor_id="passenger_front",
            seat_position="front_right",
            memory_kind="cabin_control_preference",
            content="Wrong actor preference.",
            target_temp_c=30,
            seat_heat_level=3,
        ),
    ]
    first_context, _ = context_for(
        act_key="Act 3",
        actor_id="driver_primary",
        seat_position="front_left",
        text="Use my previous comfort setup.",
        memory=StubMemory(hits=hits),
    )
    second_context, _ = context_for(
        act_key="Act 3",
        actor_id="driver_primary",
        seat_position="front_left",
        text="Use my previous comfort setup.",
        memory=StubMemory(hits=hits),
    )

    first = handle_act_03(first_context)
    second = handle_act_03(second_context)

    assert first == second
    assert first.vehicle_patch == {"drive_mode": "comfort"}
    assert first.selected_memory_ids == ["usable_drive"]


def test_act_03_is_order_independent_with_confidence_then_id_priority():
    hits = [
        raw_hit(
            "lower_cabin",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="cabin_control_preference",
            content="Lower cabin choice.",
            target_temp_c=22,
            seat_heat_level=1,
            confidence=0.7,
        ),
        raw_hit(
            "preferred_cabin",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="cabin_control_preference",
            content="Preferred cabin choice.",
            target_temp_c=26,
            seat_heat_level=2,
            confidence=0.9,
        ),
        raw_hit(
            "preferred_drive",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="driving_preference",
            content="Preferred drive choice.",
            drive_mode="eco",
            confidence=0.8,
        ),
    ]

    results = []
    for ordered_hits in (hits, list(reversed(hits))):
        context, _ = context_for(
            act_key="Act 3",
            actor_id="driver_primary",
            seat_position="front_left",
            text="Use my previous comfort setup.",
            memory=StubMemory(hits=ordered_hits),
        )
        results.append(handle_act_03(context))

    assert results[0].vehicle_patch == {
        "hvac": {"front_left_target_temp": 26},
        "seat_heat": {"front_left": 2},
        "drive_mode": "eco",
    }
    assert results[0].selected_memory_ids == [
        "preferred_cabin",
        "preferred_drive",
    ]
    assert results[0].vehicle_patch == results[1].vehicle_patch
    assert results[0].selected_memory_ids == results[1].selected_memory_ids
