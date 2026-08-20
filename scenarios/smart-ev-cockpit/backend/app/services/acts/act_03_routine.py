import re

from app.domain.memory_models import MemoryOperation
from app.domain.scenario_models import ActResult
from app.powercontext.queries import build_routine_query
from app.services.acts.base import ActContext
from app.services.acts.localization import locale_for_context, localized
from app.services.memory_ordering import memory_rank
from app.services.memory_service import MemoryService


def handle(context: ActContext) -> ActResult:
    request = context.request
    locale = locale_for_context(context)
    query = build_routine_query(
        request.actor_id,
        request.seat_position,
        request.user_id,
    )
    hits = MemoryService(context.container.powercontext_client).search(
        query=query.query,
        filters=query.filters,
        limit=query.limit,
        user_id=query.user_id,
    )
    ordered_hits = sorted(
        hits,
        key=memory_rank,
    )
    applicable = [
        hit
        for hit in ordered_hits
        if hit.metadata.actor_id == request.actor_id
        and hit.metadata.seat_position == request.seat_position
    ]
    patch: dict = {}
    selected_ids: list[str] = []
    cabin_used = False
    drive_used = False

    for hit in applicable:
        if hit.metadata.memory_kind != "cabin_control_preference":
            continue
        contributed = False
        target_temp_c = hit.metadata.target_temp_c
        if target_temp_c is None:
            target_temp_c = _content_temperature(hit.content)
        zone = hit.metadata.seat_position
        if target_temp_c is not None and zone is not None and "hvac" not in patch:
            patch["hvac"] = {
                f"{zone}_target_temp": target_temp_c
            }
            contributed = True
        seat_heat_level = hit.metadata.seat_heat_level
        if seat_heat_level is None:
            seat_heat_level = _content_seat_heat(hit.content)
        if seat_heat_level is not None and zone is not None and "seat_heat" not in patch:
            patch["seat_heat"] = {zone: seat_heat_level}
            contributed = True
        if contributed:
            selected_ids.append(hit.memory_id)
            cabin_used = True

    for hit in applicable:
        if hit.metadata.memory_kind != "driving_preference":
            continue
        drive_mode = hit.metadata.drive_mode or _content_drive_mode(hit.content)
        if drive_mode is not None:
            patch["drive_mode"] = drive_mode
            selected_ids.append(hit.memory_id)
            drive_used = True
            break

    operation = MemoryOperation(
        type="SEARCH",
        query=query.query,
        filters=query.filters,
        memory_ids=[hit.memory_id for hit in ordered_hits],
    )
    if not patch:
        return ActResult(
            act_key="Act 3",
            assistant_reply=localized(
                locale,
                en="No applicable routine was found.",
                zh="没有找到适用的组合例程。",
            ),
            memory_hits=ordered_hits,
            reason_codes=["no_applicable_memory"],
            operations=[operation],
        )

    reason_codes = [
        "complete_routine" if cabin_used and drive_used else "partial_routine"
    ]
    return ActResult(
        act_key="Act 3",
        assistant_reply=localized(
            locale,
            en="I applied the available parts of your previous routine.",
            zh="已应用你之前例程中可用的部分。",
        ),
        memory_hits=ordered_hits,
        selected_memory_ids=selected_ids,
        reason_codes=reason_codes,
        vehicle_patch=patch,
        operations=[operation],
    )


def _content_temperature(content: str) -> float | None:
    match = re.search(r"(?<!\d)(\d{1,2})(?:\s*°?\s*c)\b", content, re.IGNORECASE)
    if match is None:
        return None
    value = float(match.group(1))
    return value if 16 <= value <= 30 else None


def _content_seat_heat(content: str) -> int | None:
    match = re.search(
        r"(?:seat\s+heat(?:ing)?(?:\s+level)?|座椅加热(?:保持)?)\s*(\d+)",
        content,
        re.IGNORECASE,
    )
    if match is None:
        return None
    value = int(match.group(1))
    return value if 0 <= value <= 3 else None


def _content_drive_mode(content: str) -> str | None:
    normalized = content.casefold()
    modes = (
        ("comfort", ("comfort", "舒适")),
        ("eco", ("eco", "经济")),
        ("sport", ("sport", "运动")),
    )
    return next(
        (mode for mode, phrases in modes if any(phrase in normalized for phrase in phrases)),
        None,
    )
