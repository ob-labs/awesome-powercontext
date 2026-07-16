from pathlib import Path

from app.data.csv_snapshot_loader import CsvSnapshotLoader
from app.domain.memory_models import MemoryOperation, Recommendation
from app.domain.scenario_models import ActResult
from app.services.acts.base import ActContext
from app.services.acts.localization import Locale, locale_for_context, localized
from app.services.memory_service import MemoryService


def handle(context: ActContext) -> ActResult:
    request = context.request
    locale = locale_for_context(context)
    query = f"safe driving preference for {request.actor_id}"
    filters = {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "actor_id": request.actor_id,
        "seat_position": request.seat_position,
        "memory_kind": {"in": ["driving_preference", "emotional_preference"]},
    }
    hits = MemoryService(context.container.powermem_client).search(
        query=query,
        filters=filters,
        limit=100,
        user_id=request.user_id or request.actor_id,
    )
    ordered_hits = sorted(hits, key=lambda hit: (-hit.metadata.confidence, hit.memory_id))
    telemetry = _snapshot_loader(context).load_telemetry()
    driving = next(
        (
            hit
            for hit in ordered_hits
            if hit.metadata.memory_kind == "driving_preference"
            and hit.metadata.drive_mode is not None
            and hit.metadata.actor_id == request.actor_id
            and hit.metadata.seat_position == request.seat_position
        ),
        None,
    )
    operation = MemoryOperation(
        type="SEARCH",
        query=query,
        filters=filters,
        memory_ids=[hit.memory_id for hit in ordered_hits],
    )
    soc = telemetry.data.get("soc")
    if soc is None:
        return ActResult(
            act_key="Act 8",
            assistant_reply=localized(
                locale,
                en="Battery telemetry is unavailable, so no drive mode is suggested.",
                zh="当前没有电池遥测数据，因此不建议驾驶模式。",
            ),
            memory_hits=ordered_hits,
            reason_codes=["telemetry_missing"],
            operations=[operation],
            data_source=telemetry.source,
        )
    if driving is None:
        return ActResult(
            act_key="Act 8",
            assistant_reply=localized(
                locale,
                en="No applicable driving preference was found.",
                zh="没有找到适用的驾驶偏好。",
            ),
            memory_hits=ordered_hits,
            reason_codes=["no_applicable_memory"],
            operations=[operation],
            data_source=telemetry.source,
        )

    outside_temp = telemetry.data.get("outside_temp_c")
    mode = driving.metadata.drive_mode
    reason_codes = ["driving_preference"]
    if soc < 20:
        mode = "eco"
        reason_codes.append("low_soc")
    elif outside_temp is not None and outside_temp <= 0 and mode == "sport":
        mode = "comfort"
        reason_codes.append("cold_weather_caution")
    mode_label = _localized_mode(mode, locale)

    return ActResult(
        act_key="Act 8",
        assistant_reply=localized(
            locale,
            en=f"I recommend {mode} mode for this drive.",
            zh=f"建议本次使用{mode_label}模式。",
        ),
        memory_hits=ordered_hits,
        selected_memory_ids=[driving.memory_id],
        reason_codes=reason_codes,
        recommendations=[
            Recommendation(
                type="drive_mode",
                title=localized(
                    locale,
                    en="Drive mode suggestion",
                    zh="驾驶模式建议",
                ),
                summary=localized(
                    locale,
                    en=f"Use {mode} mode.",
                    zh=f"使用{mode_label}模式。",
                ),
                action_policy="suggest",
                reason_codes=reason_codes,
                metadata={
                    "drive_mode": mode,
                    "soc": soc,
                    "outside_temp_c": outside_temp,
                },
            )
        ],
        operations=[operation],
        data_source=telemetry.source,
    )


def _localized_mode(mode: str, locale: Locale) -> str:
    if locale != "zh":
        return mode
    return {
        "comfort": "舒适",
        "eco": "经济",
        "sport": "运动",
    }.get(mode, mode)


def _snapshot_loader(context: ActContext) -> CsvSnapshotLoader:
    injected = getattr(context.container, "csv_snapshot_loader", None)
    if injected is not None:
        return injected
    scenario_root = Path(__file__).resolve().parents[4]
    return CsvSnapshotLoader(
        scenario_root / "data" / "masked" / "vehicle.csv",
        scenario_root / "data" / "masked" / "soa.csv",
    )
