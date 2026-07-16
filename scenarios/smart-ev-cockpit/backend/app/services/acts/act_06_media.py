from app.domain.memory_models import MemoryOperation, Recommendation
from app.domain.scenario_models import ActResult
from app.services.acts.base import ActContext
from app.services.acts.localization import locale_for_context, localized
from app.services.memory_service import MemoryService

ACT_06_SEARCH_LIMIT = 500


def handle(context: ActContext) -> ActResult:
    locale = locale_for_context(context)
    query = "child-safe sleep media for child_rear_left rear_left"
    filters = {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "actor_id": "child_rear_left",
        "seat_position": "rear_left",
        "memory_kind": {"in": ["media_preference", "safety_policy"]},
    }
    hits = MemoryService(context.container.powermem_client).search(
        query=query,
        filters=filters,
        limit=ACT_06_SEARCH_LIMIT,
        user_id=_child_user_id(context),
    )
    ordered_hits = sorted(hits, key=lambda hit: (-hit.metadata.confidence, hit.memory_id))
    applicable = [
        hit
        for hit in ordered_hits
        if hit.metadata.actor_id == "child_rear_left"
        and hit.metadata.seat_position == "rear_left"
    ]
    media = next(
        (
            hit
            for hit in applicable
            if hit.metadata.memory_kind == "media_preference"
            and hit.metadata.media_volume is not None
            and hit.metadata.content_category is not None
        ),
        None,
    )
    policy = next(
        (
            hit
            for hit in applicable
            if hit.metadata.memory_kind == "safety_policy"
            and hit.metadata.max_media_volume is not None
        ),
        None,
    )
    operation = MemoryOperation(
        type="SEARCH",
        query=query,
        filters=filters,
        memory_ids=[hit.memory_id for hit in ordered_hits[:10]],
    )
    if media is None or policy is None:
        return ActResult(
            act_key="Act 6",
            assistant_reply=localized(
                locale,
                en=(
                    "No applicable child-safe media preference and safety policy were found."
                ),
                zh="没有找到适用的儿童安全媒体偏好和安全策略。",
            ),
            memory_hits=ordered_hits,
            reason_codes=["no_applicable_memory"],
            operations=[operation],
        )
    volume = media.metadata.media_volume
    selected_ids = [media.memory_id]
    reason_codes = ["child_safe_media_suggestion"]
    volume = min(volume, policy.metadata.max_media_volume)
    selected_ids.append(policy.memory_id)
    reason_codes.append("safety_volume_cap_applied")
    return ActResult(
        act_key="Act 6",
        assistant_reply=localized(
            locale,
            en="I can suggest child-safe media at a low volume.",
            zh="可以推荐低音量的儿童安全媒体。",
        ),
        memory_hits=ordered_hits,
        selected_memory_ids=selected_ids,
        reason_codes=reason_codes,
        recommendations=[
            Recommendation(
                type="media",
                title=localized(
                    locale,
                    en="Child-safe sleep media",
                    zh="儿童安全睡眠媒体",
                ),
                summary=localized(
                    locale,
                    en="Quiet child-safe content is ready for confirmation.",
                    zh="低音量儿童安全内容已准备确认。",
                ),
                action_policy="suggest",
                reason_codes=reason_codes,
                metadata={
                    "content_category": media.metadata.content_category,
                    "volume": volume,
                },
            )
        ],
        operations=[operation],
    )


def _child_user_id(context: ActContext) -> str:
    identity_service = getattr(context.container, "identity_service", None)
    if identity_service is None:
        return "child_rear_left"
    return identity_service.get_identity("child_rear_left").user_id
