import re
from datetime import UTC, datetime

from app.domain.memory_models import MemoryMetadata, MemoryOperation
from app.domain.scenario_models import ActResult
from app.services.acts.base import ActContext
from app.services.acts.localization import locale_for_context, localized
from app.services.memory_service import MemoryService

_TEMPERATURE_RE = re.compile(r"(?<!\d)(\d{1,2})(?:\s*°?\s*c)\b", re.IGNORECASE)
_SEAT_HEAT_PATTERNS = (
    re.compile(r"座椅加热\s*(\d+)\s*档"),
    re.compile(r"seat\s+heat(?:ing)?(?:\s+level)?\s*(\d+)", re.IGNORECASE),
)


def handle(context: ActContext) -> ActResult:
    locale = locale_for_context(context)
    parsed = _parse_preference(context.request.text)
    if parsed is None:
        return ActResult(
            act_key="Act 1",
            assistant_reply=localized(
                locale,
                en=(
                    "Please provide a temperature from 16C to 30C "
                    "and seat heat from 0 to 3."
                ),
                zh="请提供 16C 到 30C 的温度，以及 0 到 3 档的座椅加热。",
            ),
            reason_codes=["invalid_cabin_preference"],
        )

    target_temp_c, seat_heat_level, season = parsed
    source_event_id = (
        f"{context.request.session_id}:act_01:cabin_control_preference"
    )
    metadata = MemoryMetadata(
        actor_id=context.request.actor_id,
        seat_position=context.request.seat_position,
        session_id=context.request.session_id,
        memory_kind="cabin_control_preference",
        memory_dimension=["procedural", "environmental"],
        source_event_ids=[source_event_id],
        confidence=1.0,
        created_at=_utc_now_iso(),
        locale=locale,
        season=season,
        target_temp_c=target_temp_c,
        seat_heat_level=seat_heat_level,
    )
    content = (
        "cabin_control_preference: "
        f"actor={context.request.actor_id}; "
        f"seat={context.request.seat_position}; "
        f"season={season}; "
        f"target_temp_c={target_temp_c:g}; "
        f"seat_heat_level={seat_heat_level}"
    )
    records = MemoryService(context.container.powermem_client).add(
        content=content,
        metadata=metadata,
        user_id=context.request.user_id or context.request.actor_id,
        infer=False,
    )
    memory_ids = [record.memory_id for record in records]
    return ActResult(
        act_key="Act 1",
        assistant_reply=localized(
            locale,
            en="Your cabin preference was saved and applied.",
            zh="已保存并应用你的座舱偏好。",
        ),
        reason_codes=["cabin_preference_saved"],
        vehicle_patch={
            "hvac": {f"{context.request.seat_position}_target_temp": target_temp_c},
            "seat_heat": {context.request.seat_position: seat_heat_level},
        },
        operations=[MemoryOperation(type="ADD", memory_ids=memory_ids)],
    )


def _parse_preference(text: str) -> tuple[float, int, str] | None:
    temperature_match = _TEMPERATURE_RE.search(text)
    heat_match = next(
        (match for pattern in _SEAT_HEAT_PATTERNS if (match := pattern.search(text))),
        None,
    )
    normalized = text.casefold()
    if "冬" in normalized or "winter" in normalized:
        season = "winter"
    elif "夏" in normalized or "summer" in normalized:
        season = "summer"
    else:
        return None
    if temperature_match is None or heat_match is None:
        return None
    target_temp_c = float(temperature_match.group(1))
    seat_heat_level = int(heat_match.group(1))
    if not 16 <= target_temp_c <= 30 or not 0 <= seat_heat_level <= 3:
        return None
    return target_temp_c, seat_heat_level, season


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
