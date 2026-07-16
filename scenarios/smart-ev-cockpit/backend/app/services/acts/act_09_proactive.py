from pydantic import BaseModel, ConfigDict, Field

from app.domain.memory_models import MemoryOperation, Recommendation
from app.domain.scenario_models import ActResult
from app.services.acts.base import ActContext
from app.services.acts.localization import Locale, locale_for_context, localized
from app.services.memory_service import MemoryService


class VehicleEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    soc: float = Field(ge=0, le=100)
    range_km: float = Field(ge=0)
    text: str | None = None
    confirm_navigation: bool = False


def handle(context: ActContext, event: VehicleEvent | dict) -> ActResult:
    request = context.request
    locale = locale_for_context(context)
    vehicle_event = (
        event if isinstance(event, VehicleEvent) else VehicleEvent.model_validate(event)
    )
    patch = vehicle_event.model_dump(exclude={"text", "confirm_navigation"})
    query = f"proactive low energy support for {request.actor_id}"
    filters = {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "actor_id": request.actor_id,
        "seat_position": request.seat_position,
        "memory_kind": {
            "in": [
                "charging_preference",
                "driving_preference",
                "emotional_preference",
            ]
        },
    }
    hits = MemoryService(context.container.powermem_client).search(
        query=query,
        filters=filters,
        limit=10,
        user_id=request.user_id or request.actor_id,
    )
    ordered_hits = sorted(hits, key=lambda hit: (-hit.metadata.confidence, hit.memory_id))
    applicable = [
        hit
        for hit in ordered_hits
        if hit.metadata.actor_id == request.actor_id
        and hit.metadata.seat_position == request.seat_position
    ]
    emotion = next(
        (
            hit
            for hit in applicable
            if hit.metadata.memory_kind == "emotional_preference"
            and hit.metadata.emotional_tone is not None
        ),
        None,
    )
    charging = next(
        (
            hit
            for hit in applicable
            if hit.metadata.memory_kind == "charging_preference"
            and hit.metadata.charging_strategy is not None
        ),
        None,
    )
    selected_ids = [
        hit.memory_id for hit in ordered_hits if hit in (charging, emotion)
    ]
    reason_codes = _soc_reason_codes(vehicle_event.soc)
    recommendation = _safety_recommendation(
        vehicle_event.soc,
        vehicle_event.range_km,
        charging.metadata.charging_strategy if charging else None,
        locale,
    )
    assistant_reply = _assistant_reply(
        emotion.metadata.emotional_tone if emotion else None,
        vehicle_event.soc,
        vehicle_event.range_km,
        recommendation.summary,
        recommendation.action_policy,
        locale,
    )
    if vehicle_event.confirm_navigation and recommendation.action_policy == "confirm":
        charging_strategy = (
            charging.metadata.charging_strategy if charging else None
        )
        destination = _destination_label(charging_strategy, locale)
        selection_strategy = charging_strategy or "reachable"
        navigation_metadata = {
            "area_scope": "category",
            "destination_type": "charging_station",
            "selection_strategy": selection_strategy,
        }
        assistant_reply = localized(
            locale,
            en=f"Confirmed. Starting navigation to {destination}.",
            zh=f"已确认，开始导航到{destination}。",
        )
        recommendation = Recommendation(
            type="charging_navigation",
            title=localized(
                locale,
                en="Charging station navigation",
                zh="充电站导航",
            ),
            summary=assistant_reply,
            action_policy="execute",
            reason_codes=["critical_soc", "charging_navigation_confirmed"],
            metadata={
                "soc": vehicle_event.soc,
                "range_km": vehicle_event.range_km,
                **navigation_metadata,
            },
        )
        reason_codes = ["critical_soc", "charging_navigation_confirmed"]
        patch["navigation"] = {
            "mode": "map",
            "status": "active",
            "destination": navigation_metadata,
            "destination_label": destination,
        }
    return ActResult(
        act_key="Act 9",
        assistant_reply=assistant_reply,
        memory_hits=ordered_hits,
        selected_memory_ids=selected_ids,
        reason_codes=reason_codes,
        vehicle_patch=patch,
        recommendations=[recommendation],
        operations=[
            MemoryOperation(
                type="SEARCH",
                query=query,
                filters=filters,
                memory_ids=[hit.memory_id for hit in ordered_hits],
            ),
        ],
    )


def _soc_reason_codes(soc: float) -> list[str]:
    if soc < 10:
        return ["critical_soc"]
    if soc < 20:
        return ["low_soc"]
    return ["soc_normal"]


def _safety_recommendation(
    soc: float,
    range_km: float,
    charging_strategy: str | None,
    locale: Locale,
) -> Recommendation:
    destination = _destination_label(charging_strategy, locale)
    if soc < 10:
        summary = localized(
            locale,
            en=f"Navigate to {destination} now.",
            zh=f"请立即导航到{destination}。",
        )
        action_policy = "confirm"
    elif soc < 20:
        summary = localized(
            locale,
            en="Plan a charging stop soon and use energy-saving driving.",
            zh="请尽快规划一次充电停靠，并使用节能驾驶。",
        )
        action_policy = "suggest"
    else:
        summary = localized(
            locale,
            en="No immediate charging action is needed.",
            zh="当前不需要立即充电。",
        )
        action_policy = "inform"
    return Recommendation(
        type="charging_safety",
        title=localized(
            locale,
            en="Battery safety recommendation",
            zh="电池安全建议",
        ),
        summary=summary,
        action_policy=action_policy,
        reason_codes=_soc_reason_codes(soc),
        metadata={
            "soc": soc,
            "range_km": range_km,
            **(
                {"charging_strategy": charging_strategy}
                if charging_strategy is not None
                else {}
            ),
        },
    )


def _assistant_reply(
    tone: str | None,
    soc: float,
    range_km: float,
    recommendation_summary: str,
    action_policy: str,
    locale: Locale,
) -> str:
    status = localized(
        locale,
        en=f"Battery is at {soc:g}% with {range_km:g} km remaining. ",
        zh=f"当前电量 {soc:g}%，剩余续航 {range_km:g} 公里。",
    )
    if tone == "direct":
        tone_guidance = localized(
            locale,
            en="Follow the safety recommendation. ",
            zh="请按安全建议处理。",
        )
    elif tone in {"calm", "reassuring"}:
        tone_guidance = localized(
            locale,
            en="We can handle this safely. ",
            zh="我们可以安全处理。",
        )
    else:
        tone_guidance = ""

    summary = recommendation_summary.rstrip(".。")
    if action_policy == "confirm":
        confirmation = localized(
            locale,
            en=". Please confirm before navigation starts.",
            zh="，请确认是否开始导航。",
        )
        return f"{status}{tone_guidance}{summary}{confirmation}"
    return f"{status}{tone_guidance}{recommendation_summary}"


def _destination_label(charging_strategy: str | None, locale: Locale) -> str:
    if charging_strategy == "nearest_available":
        return localized(
            locale,
            en="the nearest available charging station",
            zh="最近可用的充电站",
        )
    return localized(
        locale,
        en="a reachable charging station",
        zh="可到达的充电站",
    )
