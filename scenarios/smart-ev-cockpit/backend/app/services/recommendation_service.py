import re

from app.domain.memory_models import MemoryRecord
from app.services.acts.localization import Locale, localized
from app.services.memory_ordering import memory_rank


class RecommendationService:
    def decide_cold_cabin_action(
        self,
        actor_id: str,
        seat_position: str,
        hits: list[MemoryRecord],
        locale: Locale = "en",
    ) -> dict:
        applicable = sorted(
            (
                hit
                for hit in hits
                if hit.metadata.actor_id == actor_id
                and hit.metadata.seat_position == seat_position
            ),
            key=memory_rank,
        )
        cabin_hits = [
            hit
            for hit in applicable
            if hit.metadata.memory_kind == "cabin_control_preference"
        ]
        patch: dict = {}
        contributing_ids: set[str] = set()
        temperature_source = next(
            (
                (hit, value)
                for hit in cabin_hits
                if (value := _target_temperature(hit)) is not None
                and hit.metadata.seat_position is not None
            ),
            None,
        )
        if temperature_source is not None:
            hit, target_temp_c = temperature_source
            zone = hit.metadata.seat_position
            patch["hvac"] = {f"{zone}_target_temp": target_temp_c}
            contributing_ids.add(hit.memory_id)

        heat_source = next(
            (
                (hit, value)
                for hit in cabin_hits
                if (value := _seat_heat_level(hit)) is not None
                and hit.metadata.seat_position is not None
            ),
            None,
        )
        sensitivity_source = next(
            (hit for hit in cabin_hits if _is_heat_sensitive(hit)),
            None,
        )
        if heat_source is not None:
            hit, seat_heat_level = heat_source
            zone = hit.metadata.seat_position
            heat_sensitive = sensitivity_source is not None
            patch["seat_heat"] = {
                zone: 0 if heat_sensitive else seat_heat_level
            }
            contributing_ids.add(hit.memory_id)
            if sensitivity_source is not None:
                contributing_ids.add(sensitivity_source.memory_id)
        if not patch:
            return _no_match_decision(locale)

        selected_ids = [
            hit.memory_id for hit in cabin_hits if hit.memory_id in contributing_ids
        ]
        reason_codes = ["cabin_preference_applied"]
        if sensitivity_source is not None and "seat_heat" in patch:
            reason_codes.append("heat_sensitivity_applied")

        restricted_controls: set[str] = set()
        policy_hits: list[MemoryRecord] = []
        for hit in applicable:
            if hit.metadata.memory_kind != "safety_policy":
                continue
            restrictions = set(
                hit.metadata.restricted_controls or _content_restricted_controls(hit.content)
            )
            if restrictions & patch.keys():
                restricted_controls.update(restrictions)
                policy_hits.append(hit)
        for control in sorted(restricted_controls):
            patch.pop(control, None)
        if policy_hits:
            selected_ids.extend(hit.memory_id for hit in policy_hits)
            reason_codes.append("safety_policy_applied")

        assistant_reply = _adjustment_reply(actor_id, patch, locale)
        return {
            "assistant_reply": assistant_reply,
            "vehicle_patch": patch,
            "selected_memory_ids": selected_ids,
            "reason_codes": reason_codes,
        }


def _no_match_decision(locale: Locale) -> dict:
    return {
        "assistant_reply": localized(
            locale,
            en="No applicable cabin preference was found.",
            zh="没有找到适用的座舱偏好。",
        ),
        "vehicle_patch": {},
        "selected_memory_ids": [],
        "reason_codes": ["no_applicable_memory"],
    }


def _content_temperature(content: str) -> float | None:
    match = re.search(r"(?<!\d)(\d{1,2})(?:\s*°?\s*c)\b", content, re.IGNORECASE)
    if match is None:
        return None
    value = float(match.group(1))
    return value if 16 <= value <= 30 else None


def _content_seat_heat(content: str) -> int | None:
    patterns = (
        r"seat\s+heat(?:ing)?(?:\s+level)?\s*(\d+)",
        r"座椅加热(?:保持)?\s*(\d+)\s*档",
    )
    match = next(
        (match for pattern in patterns if (match := re.search(pattern, content, re.IGNORECASE))),
        None,
    )
    if match is None:
        return None
    value = int(match.group(1))
    return value if 0 <= value <= 3 else None


def _content_heat_sensitive(content: str) -> bool:
    normalized = content.casefold()
    return "heat sensitive" in normalized or "怕热" in normalized


def _target_temperature(hit: MemoryRecord) -> float | None:
    return hit.metadata.target_temp_c or _content_temperature(hit.content)


def _seat_heat_level(hit: MemoryRecord) -> int | None:
    value = hit.metadata.seat_heat_level
    return value if value is not None else _content_seat_heat(hit.content)


def _is_heat_sensitive(hit: MemoryRecord) -> bool:
    return hit.metadata.heat_sensitive is True or _content_heat_sensitive(hit.content)


def _adjustment_reply(actor_id: str, patch: dict, locale: Locale) -> str:
    zone_label_zh = "主驾区域" if actor_id == "driver_primary" else "该座位"
    zone_label_en = "the driver zone" if actor_id == "driver_primary" else "this seat"
    target_temp_c = _first_patch_value(patch.get("hvac"))
    seat_heat_level = _first_patch_value(patch.get("seat_heat"))

    if locale == "zh":
        parts = []
        if target_temp_c is not None:
            parts.append(f"已将{zone_label_zh}温度调到 {_format_number(target_temp_c)}C")
        if seat_heat_level is not None:
            parts.append(f"座椅加热调到 {_format_number(seat_heat_level)} 档")
        if parts:
            return "，".join(parts) + "。"
        return localized(
            locale,
            en="I applied the available safe cabin preference for this seat.",
            zh="已为这个座位应用可用的安全座舱偏好。",
        )

    parts = []
    if target_temp_c is not None:
        parts.append(
            f"set {zone_label_en} temperature to {_format_number(target_temp_c)}C"
        )
    if seat_heat_level is not None:
        parts.append(f"set seat heat to level {_format_number(seat_heat_level)}")
    if parts:
        return "I " + " and ".join(parts) + "."
    return localized(
        locale,
        en="I applied the available safe cabin preference for this seat.",
        zh="已为这个座位应用可用的安全座舱偏好。",
    )


def _first_patch_value(values: dict | None) -> float | int | None:
    if not values:
        return None
    return next(iter(values.values()))


def _format_number(value: float | int) -> str:
    return f"{value:g}" if isinstance(value, float) else str(value)


def _content_restricted_controls(content: str) -> list[str]:
    normalized = content.casefold()
    restriction_markers = ("restrict", "must not", "禁止", "限制", "不得")
    if not any(marker in normalized for marker in restriction_markers):
        return []
    supported_phrases = {
        "hvac": ("hvac", "climate control", "空调"),
        "seat_heat": ("seat heat", "seat heating", "座椅加热"),
        "drive_mode": ("drive mode", "驾驶模式"),
    }
    return [
        control
        for control, phrases in supported_phrases.items()
        if any(phrase in normalized for phrase in phrases)
    ]
