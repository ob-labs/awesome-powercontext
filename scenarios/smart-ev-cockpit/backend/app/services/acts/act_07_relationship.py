from app.domain.memory_models import MemoryMetadata, MemoryOperation, Recommendation
from app.domain.scenario_models import ActResult
from app.services.acts.base import ActContext, safe_region_label
from app.services.acts.localization import locale_for_context, localized
from app.services.memory_service import MemoryService

SAFE_RECOMMENDATION_SUMMARIES = {
    "calm_dinner": "Consider a calm dinner tonight.",
}
SAFE_RECOMMENDATION_SUMMARIES_ZH = {
    "calm_dinner": "可以考虑今晚安排一次安静的晚餐。",
}
SAFE_HINT_RECOMMENDATIONS = {"calm dinner": "calm_dinner"}


def handle(context: ActContext) -> ActResult:
    request = context.request
    locale = locale_for_context(context)
    query = f"relationship suggestions for {request.actor_id} with region-safe context"
    filters = {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "actor_id": request.actor_id,
        "seat_position": request.seat_position,
        "memory_kind": {"in": ["relationship_event", "location_episode"]},
    }
    hits = MemoryService(context.container.powermem_client).search(
        query=query,
        filters=filters,
        limit=100,
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
        if hit.metadata.memory_kind in {"relationship_event", "location_episode"}
        else hit
        for hit in ordered_hits
    ]
    applicable = [
        hit
        for hit in presenter_hits
        if hit.metadata.actor_id == request.actor_id
        and hit.metadata.seat_position == request.seat_position
    ]
    relationship = next(
        (
            hit
            for hit in applicable
            if hit.metadata.memory_kind == "relationship_event"
            and _safe_summary(hit.metadata)
        ),
        None,
    )
    location = next(
        (
            hit
            for hit in applicable
            if hit.metadata.memory_kind == "location_episode"
            and safe_region_label(hit.metadata.region)
        ),
        None,
    )
    operation = MemoryOperation(
        type="SEARCH",
        query=query,
        filters=filters,
        memory_ids=[hit.memory_id for hit in ordered_hits],
    )
    if relationship is None:
        return ActResult(
            act_key="Act 7",
            assistant_reply=localized(
                locale,
                en="No applicable relationship suggestion was found.",
                zh="没有找到适用的关系建议。",
            ),
            memory_hits=presenter_hits,
            reason_codes=["no_applicable_memory"],
            operations=[operation],
        )
    metadata = {
        "date": "anniversary date masked",
        "area_scope": "region",
    }
    summary = _safe_summary(relationship.metadata, locale)
    selected_ids = [relationship.memory_id]
    if location is not None:
        metadata["region"] = safe_region_label(location.metadata.region)
        selected_ids.append(location.memory_id)
    return ActResult(
        act_key="Act 7",
        assistant_reply=localized(
            locale,
            en=f"{summary} I kept the anniversary date private.",
            zh=f"{summary}相关纪念日日期已保护。",
        ),
        memory_hits=presenter_hits,
        selected_memory_ids=selected_ids,
        reason_codes=["relationship_suggestion", "anniversary_date_masked"],
        recommendations=[
            Recommendation(
                type="relationship",
                title=localized(
                    locale,
                    en="Tonight's suggestion",
                    zh="今晚建议",
                ),
                summary=summary,
                action_policy="suggest",
                reason_codes=["anniversary_date_masked", "navigation_not_started"],
                metadata=metadata,
            )
        ],
        operations=[operation],
    )


def _safe_summary(metadata: MemoryMetadata, locale="en") -> str | None:
    recommendation = metadata.relationship_recommendation
    if recommendation is None:
        normalized_hint = " ".join(
            (metadata.recommendation_hint or "").casefold().split()
        )
        recommendation = SAFE_HINT_RECOMMENDATIONS.get(normalized_hint)
    summaries = (
        SAFE_RECOMMENDATION_SUMMARIES_ZH
        if locale == "zh"
        else SAFE_RECOMMENDATION_SUMMARIES
    )
    return summaries.get(recommendation)
