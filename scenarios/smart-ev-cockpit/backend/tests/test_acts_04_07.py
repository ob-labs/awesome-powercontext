from datetime import UTC, datetime
from types import SimpleNamespace

from app.data.csv_snapshot_loader import SnapshotResult
from app.domain.memory_models import MemoryMetadata
from app.domain.scenario_models import ActRequest
from app.powermem.client import PowerMemClient
from app.privacy.projection import project_memory_for_frontend
from app.services.acts.act_04_capability import handle as handle_act_04
from app.services.acts.act_05_location import handle as handle_act_05
from app.services.acts.act_06_media import handle as handle_act_06
from app.services.acts.act_07_relationship import handle as handle_act_07
from app.services.acts.base import ActContext
from app.services.seeding_service import SeedingService


class StubMemory:
    def __init__(self, hits=None):
        self.hits = list(hits or [])
        self.search_calls = []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return {"results": self.hits}


class LimitingStubMemory(StubMemory):
    def __init__(self, hits=None):
        super().__init__(hits)
        self.list_calls = []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return {"results": self.hits[: kwargs["limit"]]}

    def get_all(self, **kwargs):
        self.list_calls.append(kwargs)
        return {"results": self.hits[: kwargs["limit"]]}


class StubSnapshotLoader:
    def __init__(self, unsupported=(), source="masked_vehicle_csv"):
        self.result = SnapshotResult(
            data={
                "vehicle_id": "demo_vehicle_001",
                "display_name": "Demo EV",
                "model_family": "Demo EV",
                "platform_version": "NT2.0",
                "assistant_version": "NOMI",
                "unsupported_features": list(unsupported),
            },
            source=source,
            missing_columns=[],
        )

    def load_vehicle_profile(self):
        return self.result


def raw_hit(
    memory_id,
    *,
    actor_id,
    seat_position,
    memory_kind,
    content,
    confidence=0.8,
    **structured,
):
    return {
        "id": memory_id,
        "memory": content,
        "metadata": {
            "actor_id": actor_id,
            "seat_position": seat_position,
            "memory_kind": memory_kind,
            "confidence": confidence,
            "created_at": "2026-07-10T00:00:00Z",
            **structured,
        },
    }


def context_for(act_key, actor_id, seat_position, text, hits, loader=None):
    memory = StubMemory(hits)
    container = SimpleNamespace(
        powermem_client=PowerMemClient(memory),
        csv_snapshot_loader=loader or StubSnapshotLoader(),
    )
    return (
        ActContext(
            request=ActRequest(
                act_key=act_key,
                actor_id=actor_id,
                seat_position=seat_position,
                text=text,
                session_id="session_test",
            ),
            container=container,
        ),
        memory,
    )


def test_memory_metadata_retains_typed_act_04_07_fields():
    metadata = MemoryMetadata(
        actor_id="driver_primary",
        seat_position="front_left",
        memory_kind="location_episode",
        created_at="2026-07-10T00:00:00Z",
        capability_feature="rest_mode",
        capability_supported=True,
        capability_source_field="un_support_funcs",
        region="river district",
        place_name="Exact Bistro",
        address="88 Exact Street",
        latitude=31.2,
        longitude=121.5,
        media_volume=18,
        content_category="bedtime_story",
        max_media_volume=20,
        anniversary_date="2020-07-10",
        relationship_recommendation="calm_dinner",
        recommendation_hint="calm dinner",
    )

    dumped = metadata.model_dump(mode="json")
    assert dumped["capability_feature"] == "rest_mode"
    assert dumped["capability_supported"] is True
    assert dumped["region"] == "river district"
    assert dumped["media_volume"] == 18
    assert dumped["max_media_volume"] == 20
    assert dumped["anniversary_date"] == "2020-07-10"
    assert dumped["relationship_recommendation"] == "calm_dinner"


def test_act_04_refuses_csv_unsupported_feature_without_command():
    hits = [
        raw_hit(
            "capability_used",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="vehicle_capability",
            content="Rest mode capability record.",
            capability_feature="rest_mode",
            capability_supported=True,
            capability_source_field="un_support_funcs",
        )
    ]
    context, memory = context_for(
        "Act 4",
        "driver_primary",
        "front_left",
        "Does this vehicle support rest mode?",
        hits,
        StubSnapshotLoader(unsupported=["rest_mode"]),
    )

    result = handle_act_04(context)

    assert memory.search_calls[0]["filters"]["memory_kind"] == "vehicle_capability"
    assert result.vehicle_patch == {}
    assert result.selected_memory_ids == []
    assert result.reason_codes == ["unsupported_vehicle_feature"]
    assert "not support" in result.assistant_reply.lower()
    assert result.data_source == "masked_vehicle_csv"
    assert all(operation.type != "VEHICLE_PATCH" for operation in result.operations)


def test_act_04_selects_capability_when_memory_and_csv_both_confirm_unsupported():
    hits = [
        raw_hit(
            "capability_used",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="vehicle_capability",
            content="Rest mode is unsupported.",
            capability_feature="rest_mode",
            capability_supported=False,
        )
    ]
    context, _ = context_for(
        "Act 4",
        "driver_primary",
        "front_left",
        "Does this vehicle support rest mode?",
        hits,
        StubSnapshotLoader(unsupported=["rest_mode"]),
    )

    result = handle_act_04(context)

    assert result.reason_codes == ["unsupported_vehicle_feature"]
    assert result.selected_memory_ids == ["capability_used"]


def test_act_04_reports_supported_feature_and_packaged_fallback_source():
    hits = [
        raw_hit(
            "capability_supported",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="vehicle_capability",
            content="Rest mode is available.",
            capability_feature="rest_mode",
            capability_supported=True,
        )
    ]
    context, _ = context_for(
        "Act 4",
        "driver_primary",
        "front_left",
        "Does this vehicle support rest mode?",
        hits,
        StubSnapshotLoader(source="synthetic_fallback"),
    )

    result = handle_act_04(context)

    assert result.reason_codes == ["vehicle_feature_supported"]
    assert result.selected_memory_ids == ["capability_supported"]
    assert result.data_source == "synthetic_fallback"


def test_act_05_returns_region_only_confirm_recommendation():
    exact_values = ("Exact Bistro", "88 Exact Street", "31.234", "121.567")
    hits = [
        raw_hit(
            "location_used",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="location_episode",
            content="Exact Bistro, 88 Exact Street, 31.234, 121.567",
            region="river district",
            place_name=exact_values[0],
            address=exact_values[1],
            latitude=31.234,
            longitude=121.567,
        )
    ]
    context, memory = context_for(
        "Act 5",
        "driver_primary",
        "front_left",
        "Take me to the restaurant from last Friday.",
        hits,
    )

    result = handle_act_05(context)

    assert memory.search_calls[0]["filters"]["memory_kind"] == "location_episode"
    assert result.vehicle_patch == {}
    assert result.selected_memory_ids == ["location_used"]
    assert result.recommendations[0].action_policy == "confirm"
    assert result.recommendations[0].metadata == {
        "area_scope": "region",
        "region": "River District",
    }
    exposed = result.assistant_reply + result.recommendations[0].model_dump_json()
    assert all(value not in exposed for value in exact_values)


def test_act_05_confirmation_switches_vehicle_navigation_to_map_mode():
    exact_values = ("Exact Bistro", "88 Exact Street", "31.234", "121.567")
    hits = [
        raw_hit(
            "location_used",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="location_episode",
            content="Exact Bistro, 88 Exact Street, 31.234, 121.567",
            region="river district",
            place_name=exact_values[0],
            address=exact_values[1],
            latitude=31.234,
            longitude=121.567,
        )
    ]
    context, _ = context_for(
        "Act 5",
        "driver_primary",
        "front_left",
        "确认导航",
        hits,
    )

    result = handle_act_05(context)

    assert result.selected_memory_ids == ["location_used"]
    assert result.reason_codes == [
        "navigation_confirmed",
        "location_exact_fields_masked",
    ]
    assert result.recommendations[0].action_policy == "execute"
    assert result.recommendations[0].metadata == {
        "area_scope": "region",
        "region": "River District",
    }
    assert result.vehicle_patch == {
        "navigation": {
            "mode": "map",
            "status": "active",
            "destination": {
                "area_scope": "region",
                "region": "River District",
            },
            "destination_label": "River District",
        }
    }
    exposed = result.assistant_reply + result.recommendations[0].model_dump_json()
    assert all(value not in exposed for value in exact_values)


def test_act_05_forces_public_location_hits_to_masked_presenter_projection():
    exact_values = ("Exact Bistro", "88 Exact Street", "31.234", "121.567")
    hits = [
        raw_hit(
            "public_location",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="location_episode",
            content=", ".join(exact_values),
            visibility="public_demo",
            privacy_level="public_demo",
            is_sensitive=False,
            region="river district",
            place_name=exact_values[0],
            address=exact_values[1],
            latitude=31.234,
            longitude=121.567,
        )
    ]
    context, memory = context_for(
        "Act 5",
        "driver_primary",
        "front_left",
        "Take me to the restaurant from last Friday.",
        hits,
    )

    result = handle_act_05(context)
    projections = [project_memory_for_frontend(hit) for hit in result.memory_hits]

    assert projections[0]["content"] == "Masked location_episode memory"
    assert all(value not in projections[0]["content"] for value in exact_values)
    assert result.memory_hits[0].metadata.visibility == "masked"
    assert result.memory_hits[0].metadata.is_sensitive is True
    assert memory.hits[0]["metadata"]["visibility"] == "public_demo"
    assert memory.hits[0]["metadata"]["is_sensitive"] is False


def test_act_05_infers_controlled_region_from_masked_generated_content():
    context, _ = context_for(
        "Act 5",
        "driver_primary",
        "front_left",
        "带我去上周五那家餐厅。",
        [
            raw_hit(
                "generated_location",
                actor_id="driver_primary",
                seat_position="front_left",
                memory_kind="location_episode",
                content="驾驶员下班后经常请求前往北部科技园的脱敏目的地。",
                visibility="masked",
                privacy_level="masked",
                is_sensitive=True,
            )
        ],
    )

    result = handle_act_05(context)

    assert result.selected_memory_ids == ["generated_location"]
    assert result.recommendations[0].metadata == {
        "area_scope": "region",
        "region": "张江科学城",
    }
    assert "张江科学城" in result.assistant_reply


def test_act_05_drops_unsafe_region_values_but_keeps_generic_region_scope():
    unsafe_regions = (
        "上海迪士尼度假区",
        "欢乐谷景区",
        "88 Exact Street",
        "31.234,121.567",
        "88 Exact Street 31.234,121.567",
    )

    for index, region in enumerate(unsafe_regions):
        context, _ = context_for(
            "Act 5",
            "driver_primary",
            "front_left",
            "Take me to the remembered destination.",
            [
                raw_hit(
                    f"unsafe_location_{index}",
                    actor_id="driver_primary",
                    seat_position="front_left",
                    memory_kind="location_episode",
                    content=f"Private destination: {region}",
                    region=region,
                )
            ],
        )

        result = handle_act_05(context)

        assert result.selected_memory_ids == [f"unsafe_location_{index}"]
        assert result.recommendations[0].metadata == {"area_scope": "region"}
        exposed = result.assistant_reply + result.recommendations[0].model_dump_json()
        assert region not in exposed
        assert "region-level destination" in exposed.lower()


def test_act_05_preserves_controlled_region_label():
    context, _ = context_for(
        "Act 5",
        "driver_primary",
        "front_left",
        "Take me to the remembered destination.",
        [
            raw_hit(
                "safe_location",
                actor_id="driver_primary",
                seat_position="front_left",
                memory_kind="location_episode",
                content="Masked destination.",
                region="浦东新区",
            )
        ],
    )

    result = handle_act_05(context)

    assert result.selected_memory_ids == ["safe_location"]
    assert result.recommendations[0].metadata == {
        "area_scope": "region",
        "region": "浦东新区",
    }
    assert "浦东新区" in result.assistant_reply


def test_act_06_combines_media_with_stricter_safety_cap():
    hits = [
        raw_hit(
            "media_used",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="media_preference",
            content="Bedtime stories at volume 24.",
            media_volume=24,
            content_category="bedtime_story",
            confidence=0.9,
        ),
        raw_hit(
            "policy_used",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="safety_policy",
            content="Child-safe volume cap 16.",
            max_media_volume=16,
            confidence=0.8,
        ),
    ]
    context, memory = context_for(
        "Act 6",
        "child_rear_left",
        "rear_left",
        "Play something for the child to sleep.",
        hits,
    )

    result = handle_act_06(context)

    assert memory.search_calls[0]["filters"]["memory_kind"] == {
        "in": ["media_preference", "safety_policy"]
    }
    assert result.vehicle_patch == {}
    assert result.selected_memory_ids == ["media_used", "policy_used"]
    assert result.recommendations[0].metadata == {
        "content_category": "bedtime_story",
        "volume": 16,
    }
    assert result.recommendations[0].action_policy == "suggest"


def test_act_06_uses_current_child_identity_when_driver_requests_child_media():
    class StubIdentityService:
        def get_identity(self, actor_id):
            assert actor_id == "child_rear_left"
            return SimpleNamespace(user_id="child_live_user")

    hits = [
        raw_hit(
            "media_used",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="media_preference",
            content="Bedtime stories at volume 18.",
            media_volume=18,
            content_category="bedtime_story",
        ),
        raw_hit(
            "policy_used",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="safety_policy",
            content="Child-safe volume cap 16.",
            max_media_volume=16,
        ),
    ]
    memory = StubMemory(hits)
    container = SimpleNamespace(
        powermem_client=PowerMemClient(memory),
        csv_snapshot_loader=StubSnapshotLoader(),
        identity_service=StubIdentityService(),
    )
    context = ActContext(
        request=ActRequest(
            act_key="Act 6",
            actor_id="driver_primary",
            user_id="driver_primary",
            seat_position="front_left",
            text="放点适合孩子睡觉的内容。",
            session_id="session_test",
        ),
        container=container,
    )

    result = handle_act_06(context)

    assert memory.search_calls[0]["user_id"] == "child_live_user"
    assert result.selected_memory_ids == ["media_used", "policy_used"]


def test_act_06_finds_structured_child_media_when_generated_hits_crowd_top_results():
    noisy_hits = [
        raw_hit(
            f"generated_noise_{index}",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="media_preference" if index % 2 == 0 else "safety_policy",
            content=f"Generated child media or policy row {index}.",
            confidence=0.96 - index * 0.001,
        )
        for index in range(20)
    ]
    valid_hits = [
        raw_hit(
            "seed_media_child_sleep",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="media_preference",
            content="The rear child prefers quiet bedtime stories.",
            media_volume=18,
            content_category="bedtime_story",
            confidence=0.8,
        ),
        raw_hit(
            "seed_safety_child_volume",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="safety_policy",
            content="Child media volume must not exceed the safe cap.",
            max_media_volume=16,
            confidence=0.8,
        ),
    ]
    memory = LimitingStubMemory([*noisy_hits, *valid_hits])
    container = SimpleNamespace(
        powermem_client=PowerMemClient(memory),
        csv_snapshot_loader=StubSnapshotLoader(),
    )
    context = ActContext(
        request=ActRequest(
            act_key="Act 6",
            actor_id="child_rear_left",
            seat_position="rear_left",
            text="Play something for the child to sleep.",
            session_id="session_test",
        ),
        container=container,
    )

    result = handle_act_06(context)

    assert memory.search_calls[0]["limit"] > 20
    assert result.selected_memory_ids == [
        "seed_media_child_sleep",
        "seed_safety_child_volume",
    ]
    assert result.recommendations[0].metadata == {
        "content_category": "bedtime_story",
        "volume": 16,
    }


def test_act_06_no_applicable_memory_is_explicit():
    context, _ = context_for(
        "Act 6",
        "child_rear_left",
        "rear_left",
        "Play something for the child to sleep.",
        [],
    )

    result = handle_act_06(context)

    assert result.recommendations == []
    assert result.selected_memory_ids == []
    assert result.reason_codes == ["no_applicable_memory"]


def test_act_06_requires_safety_policy_to_make_recommendation():
    hits = [
        raw_hit(
            "media_without_policy",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="media_preference",
            content="Bedtime stories at volume 18.",
            media_volume=18,
            content_category="bedtime_story",
        )
    ]
    context, _ = context_for(
        "Act 6",
        "child_rear_left",
        "rear_left",
        "Play something for the child to sleep.",
        hits,
    )

    result = handle_act_06(context)

    assert result.recommendations == []
    assert result.selected_memory_ids == []
    assert result.reason_codes == ["no_applicable_memory"]


def test_act_06_only_safety_policy_is_not_applicable():
    hits = [
        raw_hit(
            "policy_without_media",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="safety_policy",
            content="Child-safe volume cap 16.",
            max_media_volume=16,
        )
    ]
    context, _ = context_for(
        "Act 6",
        "child_rear_left",
        "rear_left",
        "Play something for the child to sleep.",
        hits,
    )

    result = handle_act_06(context)

    assert result.recommendations == []
    assert result.selected_memory_ids == []
    assert result.reason_codes == ["no_applicable_memory"]


def test_act_06_selects_policy_stably_by_hit_priority():
    hits = [
        raw_hit(
            "media",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="media_preference",
            content="Bedtime stories at volume 24.",
            media_volume=24,
            content_category="bedtime_story",
            confidence=0.9,
        ),
        raw_hit(
            "z_policy",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="safety_policy",
            content="Volume cap 12.",
            max_media_volume=12,
            confidence=0.8,
        ),
        raw_hit(
            "a_policy",
            actor_id="child_rear_left",
            seat_position="rear_left",
            memory_kind="safety_policy",
            content="Volume cap 16.",
            max_media_volume=16,
            confidence=0.8,
        ),
    ]
    context, _ = context_for(
        "Act 6",
        "child_rear_left",
        "rear_left",
        "Play something for the child to sleep.",
        hits,
    )

    result = handle_act_06(context)

    assert result.selected_memory_ids == ["media", "a_policy"]
    assert result.recommendations[0].metadata["volume"] == 16


def test_act_07_masks_date_and_only_suggests_cards():
    hits = [
        raw_hit(
            "relationship_used",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="relationship_event",
            content="Anniversary on 2020-07-10; calm dinner.",
            anniversary_date="2020-07-10",
            recommendation_hint="calm dinner",
            confidence=0.9,
        ),
        raw_hit(
            "region_used",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="location_episode",
            content="Masked destination.",
            region="river district",
            confidence=0.8,
        ),
    ]
    context, memory = context_for(
        "Act 7",
        "driver_primary",
        "front_left",
        "今晚有什么安排建议？",
        hits,
    )

    result = handle_act_07(context)

    assert memory.search_calls[0]["filters"]["memory_kind"] == {
        "in": ["relationship_event", "location_episode"]
    }
    assert result.vehicle_patch == {}
    assert result.selected_memory_ids == ["relationship_used", "region_used"]
    assert result.recommendations
    assert all(card.action_policy == "suggest" for card in result.recommendations)
    assert result.assistant_reply == (
        "可以考虑今晚安排一次安静的晚餐。相关纪念日日期已保护。"
    )
    exposed = result.assistant_reply + "".join(
        card.model_dump_json() for card in result.recommendations
    )
    assert "2020-07-10" not in exposed
    assert "2020" not in exposed


def test_act_07_searches_past_legacy_relationship_rows_without_safe_metadata():
    hits = [
        raw_hit(
            f"legacy_relationship_{index}",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="relationship_event",
            content="Legacy generated relationship memory without structured hint.",
            confidence=0.96,
        )
        for index in range(12)
    ]
    hits.append(
        raw_hit(
            "relationship_used",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="relationship_event",
            content="Structured relationship recommendation.",
            relationship_recommendation="calm_dinner",
            recommendation_hint="calm dinner",
            confidence=0.8,
        )
    )
    memory = LimitingStubMemory(hits)
    container = SimpleNamespace(
        powermem_client=PowerMemClient(memory),
        csv_snapshot_loader=StubSnapshotLoader(),
    )
    context = ActContext(
        request=ActRequest(
            act_key="Act 7",
            actor_id="driver_primary",
            seat_position="front_left",
            text="Any plan for tonight?",
            session_id="session_test",
        ),
        container=container,
    )

    result = handle_act_07(context)

    assert memory.search_calls[0]["limit"] > 12
    assert result.selected_memory_ids == ["relationship_used"]
    assert result.recommendations[0].summary == "Consider a calm dinner tonight."


def test_act_07_rebuilds_hint_from_whitelist_without_date_or_location_details():
    leaks = (
        "2020-07-10",
        "2020/07/10",
        "July 10, 2020",
        "10 July 2020",
        "Exact Bistro",
        "88 Exact Street",
        "31.234",
        "121.567",
    )
    hits = [
        raw_hit(
            "relationship_with_leaks",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="relationship_event",
            content="Private relationship details.",
            relationship_recommendation="calm_dinner",
            recommendation_hint="calm dinner; " + "; ".join(leaks),
            place_name="Exact Bistro",
            address="88 Exact Street",
            latitude=31.234,
            longitude=121.567,
        )
    ]
    context, _ = context_for(
        "Act 7",
        "driver_primary",
        "front_left",
        "Any plan for tonight?",
        hits,
    )

    result = handle_act_07(context)

    exposed = result.assistant_reply + "".join(
        card.model_dump_json() for card in result.recommendations
    )
    assert result.recommendations[0].summary == "Consider a calm dinner tonight."
    assert all(value not in exposed for value in leaks)


def test_act_07_masks_public_relationship_and_location_hits_for_projection():
    leaks = (
        "Anniversary on July 10, 2020",
        "Exact Bistro",
        "88 Exact Street",
        "31.234",
        "121.567",
    )
    hits = [
        raw_hit(
            "public_relationship",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="relationship_event",
            content=leaks[0],
            visibility="public_demo",
            privacy_level="public_demo",
            is_sensitive=False,
            relationship_recommendation="calm_dinner",
        ),
        raw_hit(
            "public_location",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="location_episode",
            content=", ".join(leaks[1:]),
            visibility="public_demo",
            privacy_level="public_demo",
            is_sensitive=False,
            region="River District",
            place_name=leaks[1],
            address=leaks[2],
            latitude=31.234,
            longitude=121.567,
        ),
    ]
    context, memory = context_for(
        "Act 7",
        "driver_primary",
        "front_left",
        "Any plan for tonight?",
        hits,
    )

    result = handle_act_07(context)
    projections = [project_memory_for_frontend(hit) for hit in result.memory_hits]

    assert {item["content"] for item in projections} == {
        "Masked relationship_event memory",
        "Masked location_episode memory",
    }
    assert all(
        leak not in item["content"] for leak in leaks for item in projections
    )
    assert all(hit.metadata.visibility == "masked" for hit in result.memory_hits)
    assert all(hit.metadata.is_sensitive is True for hit in result.memory_hits)
    assert all(row["metadata"]["visibility"] == "public_demo" for row in memory.hits)


def test_act_07_drops_polluted_region_values():
    polluted_regions = (
        "浦东新区88号",
        "River District 31.234",
        "88 Exact Street",
        "Exact Bistro District",
    )

    for index, region in enumerate(polluted_regions):
        hits = [
            raw_hit(
                f"relationship_{index}",
                actor_id="driver_primary",
                seat_position="front_left",
                memory_kind="relationship_event",
                content="Safe structured recommendation.",
                relationship_recommendation="calm_dinner",
            ),
            raw_hit(
                f"location_{index}",
                actor_id="driver_primary",
                seat_position="front_left",
                memory_kind="location_episode",
                content="Private exact destination.",
                region=region,
            ),
        ]
        context, _ = context_for(
            "Act 7",
            "driver_primary",
            "front_left",
            "Any plan for tonight?",
            hits,
        )

        result = handle_act_07(context)

        assert result.selected_memory_ids == [f"relationship_{index}"]
        assert result.recommendations[0].metadata["area_scope"] == "region"
        assert "region" not in result.recommendations[0].metadata
        assert region not in result.recommendations[0].model_dump_json()


def test_act_07_rejects_scenic_spots_that_look_like_chinese_regions():
    for index, region in enumerate(("欢乐谷景区", "上海迪士尼度假区")):
        hits = [
            raw_hit(
                f"relationship_scenic_{index}",
                actor_id="driver_primary",
                seat_position="front_left",
                memory_kind="relationship_event",
                content="Safe structured recommendation.",
                relationship_recommendation="calm_dinner",
            ),
            raw_hit(
                f"location_scenic_{index}",
                actor_id="driver_primary",
                seat_position="front_left",
                memory_kind="location_episode",
                content="Private scenic destination.",
                region=region,
            ),
        ]
        context, _ = context_for(
            "Act 7",
            "driver_primary",
            "front_left",
            "Any plan for tonight?",
            hits,
        )

        result = handle_act_07(context)

        assert result.selected_memory_ids == [f"relationship_scenic_{index}"]
        assert result.recommendations[0].metadata == {
            "date": "anniversary date masked",
            "area_scope": "region",
        }
        assert region not in result.recommendations[0].model_dump_json()


def test_act_07_accepts_only_controlled_chinese_and_english_regions():
    expected_regions = {
        "浦东新区": "浦东新区",
        "Pudong New Area": "Pudong New Area",
        "river district": "River District",
    }

    for index, (region, expected) in enumerate(expected_regions.items()):
        hits = [
            raw_hit(
                f"relationship_safe_region_{index}",
                actor_id="driver_primary",
                seat_position="front_left",
                memory_kind="relationship_event",
                content="Safe structured recommendation.",
                relationship_recommendation="calm_dinner",
            ),
            raw_hit(
                f"location_safe_region_{index}",
                actor_id="driver_primary",
                seat_position="front_left",
                memory_kind="location_episode",
                content="Masked regional context.",
                region=region,
            ),
        ]
        context, _ = context_for(
            "Act 7",
            "driver_primary",
            "front_left",
            "Any plan for tonight?",
            hits,
        )

        result = handle_act_07(context)

        assert result.selected_memory_ids == [
            f"relationship_safe_region_{index}",
            f"location_safe_region_{index}",
        ]
        assert result.recommendations[0].metadata["area_scope"] == "region"
        assert result.recommendations[0].metadata["region"] == expected


def test_act_07_text_fallback_requires_exact_normalized_phrase():
    exact_context, _ = context_for(
        "Act 7",
        "driver_primary",
        "front_left",
        "Any plan for tonight?",
        [
            raw_hit(
                "exact_hint",
                actor_id="driver_primary",
                seat_position="front_left",
                memory_kind="relationship_event",
                content="Safe fallback.",
                recommendation_hint="  CALM   DINNER  ",
            )
        ],
    )
    negated_context, _ = context_for(
        "Act 7",
        "driver_primary",
        "front_left",
        "Any plan for tonight?",
        [
            raw_hit(
                "negated_hint",
                actor_id="driver_primary",
                seat_position="front_left",
                memory_kind="relationship_event",
                content="Do not use this suggestion.",
                recommendation_hint="do not suggest calm dinner",
            )
        ],
    )

    exact = handle_act_07(exact_context)
    negated = handle_act_07(negated_context)

    assert exact.selected_memory_ids == ["exact_hint"]
    assert exact.recommendations[0].summary == "Consider a calm dinner tonight."
    assert negated.selected_memory_ids == []
    assert negated.recommendations == []
    assert negated.reason_codes == ["no_applicable_memory"]


def test_act_07_missing_recommendation_metadata_is_not_applicable():
    hits = [
        raw_hit(
            "relationship_without_hint",
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind="relationship_event",
            content="Private relationship details.",
        )
    ]
    context, _ = context_for(
        "Act 7",
        "driver_primary",
        "front_left",
        "Any plan for tonight?",
        hits,
    )

    result = handle_act_07(context)

    assert result.recommendations == []
    assert result.selected_memory_ids == []
    assert result.reason_codes == ["no_applicable_memory"]


def test_all_handlers_are_order_independent():
    cases = [
        (
            handle_act_04,
            context_for(
                "Act 4",
                "driver_primary",
                "front_left",
                "Does this vehicle support rest mode?",
                [
                    raw_hit(
                        "z_cap",
                        actor_id="driver_primary",
                        seat_position="front_left",
                        memory_kind="vehicle_capability",
                        content="Lower priority.",
                        capability_feature="rest_mode",
                        capability_supported=False,
                        confidence=0.7,
                    ),
                    raw_hit(
                        "a_cap",
                        actor_id="driver_primary",
                        seat_position="front_left",
                        memory_kind="vehicle_capability",
                        content="Higher priority.",
                        capability_feature="rest_mode",
                        capability_supported=True,
                        confidence=0.9,
                    ),
                ],
            )[0],
        ),
        (
            handle_act_05,
            context_for(
                "Act 5",
                "driver_primary",
                "front_left",
                "Restaurant",
                [
                    raw_hit(
                        "z_location",
                        actor_id="driver_primary",
                        seat_position="front_left",
                        memory_kind="location_episode",
                        content="Other.",
                        region="west city area",
                        confidence=0.7,
                    ),
                    raw_hit(
                        "a_location",
                        actor_id="driver_primary",
                        seat_position="front_left",
                        memory_kind="location_episode",
                        content="Preferred.",
                        region="river district",
                        confidence=0.9,
                    ),
                ],
            )[0],
        ),
        (
            handle_act_06,
            context_for(
                "Act 6",
                "child_rear_left",
                "rear_left",
                "Sleep media",
                [
                    raw_hit(
                        "media",
                        actor_id="child_rear_left",
                        seat_position="rear_left",
                        memory_kind="media_preference",
                        content="Story.",
                        media_volume=18,
                        content_category="bedtime_story",
                    ),
                    raw_hit(
                        "policy",
                        actor_id="child_rear_left",
                        seat_position="rear_left",
                        memory_kind="safety_policy",
                        content="Cap.",
                        max_media_volume=16,
                    ),
                ],
            )[0],
        ),
        (
            handle_act_07,
            context_for(
                "Act 7",
                "driver_primary",
                "front_left",
                "Tonight",
                [
                    raw_hit(
                        "relationship",
                        actor_id="driver_primary",
                        seat_position="front_left",
                        memory_kind="relationship_event",
                        content="Hint.",
                        recommendation_hint="calm dinner",
                    ),
                    raw_hit(
                        "location",
                        actor_id="driver_primary",
                        seat_position="front_left",
                        memory_kind="location_episode",
                        content="Region.",
                        region="river district",
                    ),
                ],
            )[0],
        ),
    ]

    for handler, context in cases:
        forward = handler(context)
        reversed_memory = StubMemory(
            [
                {
                    "id": hit.memory_id,
                    "memory": hit.content,
                    "metadata": hit.metadata.model_dump(mode="json"),
                }
                for hit in reversed(forward.memory_hits)
            ]
        )
        reversed_context = ActContext(
            request=context.request,
            container=SimpleNamespace(
                powermem_client=PowerMemClient(reversed_memory),
                csv_snapshot_loader=context.container.csv_snapshot_loader,
            ),
        )
        backward = handler(reversed_context)
        assert forward == backward


class SeedRecordingMemory:
    def __init__(self):
        self.add_calls = []

    def get_all(self, **kwargs):
        return {"results": []}

    def add(self, content, **kwargs):
        self.add_calls.append({"content": content, **kwargs})
        return {"results": [{"id": f"seed_{len(self.add_calls)}"}]}


def test_seeds_cover_all_queried_kinds_with_inference_disabled():
    memory = SeedRecordingMemory()

    SeedingService(memory).seed()

    kinds = {call["metadata"]["memory_kind"] for call in memory.add_calls}
    assert kinds >= {
        "cabin_control_preference",
        "vehicle_capability",
        "driving_preference",
        "location_episode",
        "media_preference",
        "safety_policy",
        "relationship_event",
    }
    driving_calls = [
        call
        for call in memory.add_calls
        if call["metadata"]["memory_kind"] == "driving_preference"
    ]
    assert driving_calls
    assert all(call["metadata"]["drive_mode"] == "comfort" for call in driving_calls)
    assert all(call["infer"] is False for call in memory.add_calls)
    assert all(call["metadata"]["source_event_ids"] for call in memory.add_calls)


class UpgradeSeedMemory:
    def __init__(self):
        self.rows_by_source_id = {
            "dlg_0001": {
                "id": "seed_existing_cabin",
                "metadata": {"source_event_ids": ["dlg_0001"]},
            }
        }
        self.add_calls = []
        self.get_all_calls = []

    def get_all(self, **kwargs):
        self.get_all_calls.append(kwargs)
        source_ids = kwargs["filters"]["source_event_ids"]
        row = self.rows_by_source_id.get(source_ids[0])
        return {"results": [row] if row else []}

    def add(self, content, **kwargs):
        self.add_calls.append({"content": content, **kwargs})
        source_id = kwargs["metadata"]["source_event_ids"][0]
        row = {
            "id": f"seed_{source_id}",
            "metadata": kwargs["metadata"],
        }
        self.rows_by_source_id[source_id] = row
        return {"results": [row]}


def test_seeding_upgrades_old_cabin_database_and_is_idempotent_by_source_id():
    memory = UpgradeSeedMemory()
    generated_at = datetime(2026, 7, 12, 8, 10, tzinfo=UTC)

    first = SeedingService(memory, generated_at=generated_at).seed()
    first_add_count = len(memory.add_calls)
    second = SeedingService(memory, generated_at=generated_at).seed()

    expected_seed_source_ids = {
        "dlg_0001_summer",
        "seed_capability_rest_mode",
        "seed_driving_comfort_mode",
        "seed_location_restaurant",
        "seed_media_child_sleep",
        "seed_safety_child_volume",
        "seed_relationship_anniversary",
    }
    expected_stored_source_ids = {
        "dlg_0001",
        *expected_seed_source_ids,
    }
    assert first["seeded"] is True
    assert second["seeded"] is False
    assert set(memory.rows_by_source_id) == expected_stored_source_ids
    assert first_add_count == len(expected_seed_source_ids)
    assert len(memory.add_calls) == first_add_count
    assert {
        call["filters"]["source_event_ids"][0] for call in memory.get_all_calls
    } == expected_seed_source_ids
