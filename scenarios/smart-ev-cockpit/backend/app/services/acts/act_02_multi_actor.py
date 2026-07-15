from app.domain.memory_models import MemoryOperation
from app.domain.scenario_models import ActResult
from app.powermem.queries import build_act_02_query
from app.services.acts.base import ActContext
from app.services.acts.localization import locale_for_context
from app.services.memory_ordering import memory_rank
from app.services.memory_service import MemoryService
from app.services.recommendation_service import RecommendationService


def handle(context: ActContext) -> ActResult:
    request = context.request
    query = build_act_02_query(
        request.actor_id,
        request.seat_position,
        request.user_id,
    )
    hits = MemoryService(context.container.powermem_client).search(
        query=query.query,
        filters=query.filters,
        limit=query.limit,
        user_id=query.user_id,
    )
    ordered_hits = sorted(
        hits,
        key=memory_rank,
    )
    decision = RecommendationService().decide_cold_cabin_action(
        actor_id=request.actor_id,
        seat_position=request.seat_position,
        hits=ordered_hits,
        locale=locale_for_context(context),
    )
    return ActResult(
        act_key="Act 2",
        assistant_reply=decision["assistant_reply"],
        memory_hits=ordered_hits,
        selected_memory_ids=decision["selected_memory_ids"],
        reason_codes=decision["reason_codes"],
        vehicle_patch=decision["vehicle_patch"],
        operations=[
            MemoryOperation(
                type="SEARCH",
                query=query.query,
                filters=query.filters,
                memory_ids=[hit.memory_id for hit in ordered_hits],
            )
        ],
    )
