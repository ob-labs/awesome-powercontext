from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.domain.scenario_models import ScenarioClock
from app.services.cockpit_service import CockpitService, LifecycleMutationError, UtterRequest

router = APIRouter(prefix="/api/scenarios/smart-ev-cockpit")


@router.post("/utter", response_model=None)
def utter(payload: UtterRequest, request: Request) -> dict | JSONResponse:
    try:
        return CockpitService(request.app.state.container).handle_utter(payload)
    except LifecycleMutationError as exc:
        return JSONResponse(status_code=409, content=exc.response)


@router.get("/chat-history")
def chat_history(
    session_id: str,
    request: Request,
    actor_id: str | None = None,
    user_id: str | None = None,
    limit: int = 100,
) -> dict:
    messages = request.app.state.container.chat_history_service.list_messages(
        session_id=session_id,
        actor_id=actor_id,
        user_id=user_id,
        limit=limit,
    )
    return {"messages": [message.model_dump() for message in messages]}


@router.get("/state")
def state(request: Request) -> dict:
    container = request.app.state.container
    return {
        "scenario_day": container.scenario_clock.current_day,
        "vehicle_state": container.vehicle_state_service.current_state(),
        "recent_operations": container.journal_service.recent(),
    }


@router.post("/lifecycle/run", response_model=None)
def lifecycle_run(payload: ScenarioClock, request: Request) -> dict | JSONResponse:
    container = request.app.state.container
    try:
        return CockpitService(container).handle_lifecycle(payload)
    except LifecycleMutationError as exc:
        return JSONResponse(status_code=409, content=exc.response)
