from pathlib import Path

from app.data.csv_snapshot_loader import CsvSnapshotLoader
from app.domain.memory_models import MemoryOperation, Recommendation
from app.domain.scenario_models import ActResult
from app.services.acts.base import ActContext
from app.services.acts.localization import locale_for_context, localized
from app.services.memory_service import MemoryService


def handle(context: ActContext) -> ActResult:
    request = context.request
    locale = locale_for_context(context)
    query = f"vehicle capability rest_mode for {request.actor_id}"
    filters = {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "memory_kind": "vehicle_capability",
    }
    hits = MemoryService(context.container.powermem_client).search(
        query=query,
        filters=filters,
        limit=10,
        user_id=request.user_id or request.actor_id,
    )
    ordered_hits = sorted(hits, key=lambda hit: (-hit.metadata.confidence, hit.memory_id))
    capability = next(
        (
            hit
            for hit in ordered_hits
            if hit.metadata.memory_kind == "vehicle_capability"
            and hit.metadata.capability_feature == "rest_mode"
        ),
        None,
    )
    snapshot = _snapshot_loader(context).load_vehicle_profile()
    operation = MemoryOperation(
        type="SEARCH",
        query=query,
        filters=filters,
        memory_ids=[hit.memory_id for hit in ordered_hits],
    )
    unsupported = "rest_mode" in snapshot.data.get("unsupported_features", [])
    if unsupported:
        selected_ids = (
            [capability.memory_id]
            if capability is not None
            and capability.metadata.capability_supported is False
            else []
        )
        return ActResult(
            act_key="Act 4",
            assistant_reply=localized(
                locale,
                en="This vehicle does not support rest mode.",
                zh="这辆车不支持休息模式。",
            ),
            memory_hits=ordered_hits,
            selected_memory_ids=selected_ids,
            reason_codes=["unsupported_vehicle_feature"],
            operations=[operation],
            data_source=snapshot.source,
        )
    if capability is None or capability.metadata.capability_supported is not True:
        return ActResult(
            act_key="Act 4",
            assistant_reply=localized(
                locale,
                en="No applicable rest mode capability record was found.",
                zh="没有找到适用的休息模式能力记录。",
            ),
            memory_hits=ordered_hits,
            reason_codes=["no_applicable_memory"],
            operations=[operation],
            data_source=snapshot.source,
        )
    selected_ids = [capability.memory_id]
    return ActResult(
        act_key="Act 4",
        assistant_reply=localized(
            locale,
            en="This vehicle supports rest mode.",
            zh="这辆车支持休息模式。",
        ),
        memory_hits=ordered_hits,
        selected_memory_ids=selected_ids,
        reason_codes=["vehicle_feature_supported"],
        recommendations=[
            Recommendation(
                type="vehicle_capability",
                title=localized(
                    locale,
                    en="Rest mode available",
                    zh="休息模式可用",
                ),
                summary=localized(
                    locale,
                    en="Rest mode is supported on this vehicle.",
                    zh="这辆车支持休息模式。",
                ),
                action_policy="inform",
                reason_codes=["vehicle_feature_supported"],
                metadata={"feature": "rest_mode"},
            )
        ],
        operations=[operation],
        data_source=snapshot.source,
    )


def _snapshot_loader(context: ActContext) -> CsvSnapshotLoader:
    injected = getattr(context.container, "csv_snapshot_loader", None)
    if injected is not None:
        return injected
    scenario_root = Path(__file__).resolve().parents[4]
    return CsvSnapshotLoader(
        scenario_root / "data" / "masked" / "vehicle.csv",
        scenario_root / "data" / "masked" / "soa.csv",
    )
