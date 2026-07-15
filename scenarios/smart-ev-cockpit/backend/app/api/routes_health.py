from fastapi import APIRouter

from app.settings import get_settings

router = APIRouter()


@router.get("/api/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "smart-ev-cockpit-backend",
        "scenario_id": settings.scenario_id,
    }
