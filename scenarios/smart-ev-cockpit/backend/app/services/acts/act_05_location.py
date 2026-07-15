from app.domain.memory_models import MemoryOperation, Recommendation
from app.domain.scenario_models import ActResult
from app.services.acts.base import (
    ActContext,
    safe_region_label,
    safe_region_label_from_text,
)
from app.services.acts.localization import locale_for_context, localized
from app.services.memory_service import MemoryService

_NAVIGATION_CONFIRMATION_PHRASES = (
    "确认导航",
    "开始导航",
    "确认路线",
    "confirm navigation",
    "start navigation",
    "confirm route",
)


def handle(context: ActContext) -> ActResult:
    request = context.request
    locale = locale_for_context(context)
    is_confirmation = _is_navigation_confirmation(request.text)
    query = f"region-level location recall for {request.actor_id} {request.seat_position}"
    filters = {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "actor_id": request.actor_id,
        "seat_position": request.seat_position,
        "memory_kind": "location_episode",
    }
    hits = MemoryService(context.container.powermem_client).search(
        query=query,
        filters=filters,
        limit=10,
        user_id=request.user_id or request.actor_id,
    )
    ordered_hits = sorted(hits, key=lambda hit: (-hit.metadata.confidence, hit.memory_id))
    presenter_hits = [
        hit.model_copy(
            update={
                "metadata": hit.metadata.model_copy(
                    update={
                        "visibility": "masked",
                        "privacy_level": "masked",
                        "is_sensitive": True,
                    }
                )
            }
        )
        if hit.metadata.memory_kind == "location_episode"
        else hit
        for hit in ordered_hits
    ]
    selected = next(
        (
            hit
            for hit in presenter_hits
            if hit.metadata.memory_kind == "location_episode"
            and hit.metadata.actor_id == request.actor_id
            and hit.metadata.seat_position == request.seat_position
            and _region_candidate(hit)
        ),
        None,
    )
    operation = MemoryOperation(
        type="SEARCH",
        query=query,
        filters=filters,
        memory_ids=[hit.memory_id for hit in ordered_hits],
    )
    if selected is None:
        return ActResult(
            act_key="Act 5",
            assistant_reply=localized(
                locale,
                en="No region-safe destination memory was found.",
                zh="没有找到区域级安全的目的地记忆。",
            ),
            memory_hits=presenter_hits,
            reason_codes=["no_applicable_memory"],
            operations=[operation],
        )
    region = safe_region_label(_region_candidate(selected))
    recommendation_metadata = {"area_scope": "region"}
    assistant_reply = localized(
        locale,
        en="I found a region-level destination memory. Confirm navigation?",
        zh="我找到一个区域级目的地记忆。是否确认导航？",
    )
    summary = localized(
        locale,
        en="Navigate to the remembered region-level destination.",
        zh="导航到记忆中的区域级目的地。",
    )
    if region is not None:
        recommendation_metadata["region"] = region
        assistant_reply = localized(
            locale,
            en=f"I found a destination memory in the {region}. Confirm navigation?",
            zh=f"我找到了{region}的目的地记忆。是否确认导航？",
        )
        summary = localized(
            locale,
            en=f"Navigate to the remembered destination in the {region}.",
            zh=f"导航到记忆中位于{region}的目的地。",
        )
    if is_confirmation:
        destination_label = region or localized(
            locale,
            en="region-level destination",
            zh="区域级目的地",
        )
        route_summary = localized(
            locale,
            en=f"Map mode is active for {destination_label}.",
            zh=f"已切换到地图模式，开始导航到{destination_label}。",
        )
        return ActResult(
            act_key="Act 5",
            assistant_reply=route_summary,
            memory_hits=presenter_hits,
            selected_memory_ids=[selected.memory_id],
            reason_codes=["navigation_confirmed", "location_exact_fields_masked"],
            vehicle_patch={
                "navigation": {
                    "mode": "map",
                    "status": "active",
                    "destination": recommendation_metadata,
                    "destination_label": destination_label,
                }
            },
            recommendations=[
                Recommendation(
                    type="navigation",
                    title=localized(
                        locale,
                        en="Region-level navigation",
                        zh="区域级导航",
                    ),
                    summary=route_summary,
                    action_policy="execute",
                    reason_codes=[
                        "location_exact_fields_masked",
                        "navigation_confirmed",
                    ],
                    metadata=recommendation_metadata,
                )
            ],
            operations=[operation],
        )
    return ActResult(
        act_key="Act 5",
        assistant_reply=assistant_reply,
        memory_hits=presenter_hits,
        selected_memory_ids=[selected.memory_id],
        reason_codes=["region_navigation_confirmation"],
        recommendations=[
            Recommendation(
                type="navigation",
                title=localized(
                    locale,
                    en="Region-level destination",
                    zh="区域级目的地",
                ),
                summary=summary,
                action_policy="confirm",
                reason_codes=["location_exact_fields_masked"],
                metadata=recommendation_metadata,
            )
        ],
        operations=[operation],
    )


def _region_candidate(hit) -> str | None:
    return hit.metadata.region or safe_region_label_from_text(hit.content)


def _is_navigation_confirmation(text: str) -> bool:
    normalized = " ".join(text.casefold().split())
    return any(phrase in normalized for phrase in _NAVIGATION_CONFIRMATION_PHRASES)
