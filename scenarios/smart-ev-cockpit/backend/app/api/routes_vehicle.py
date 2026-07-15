from fastapi import APIRouter, Request

from app.services.acts.act_09_proactive import VehicleEvent
from app.services.cockpit_service import CockpitService

router = APIRouter(prefix="/api/scenarios/smart-ev-cockpit")


@router.post("/events/vehicle")
def vehicle_event(payload: VehicleEvent, request: Request) -> dict:
    return CockpitService(request.app.state.container).handle_vehicle_event(payload)
