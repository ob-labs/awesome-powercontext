from fastapi import APIRouter, HTTPException, Request

from app.domain.identity_models import UpdateUserIdentityRequest
from app.powercontext.client import PowerContextConnectionError
from app.services.identity_service import UnknownIdentityError

router = APIRouter(prefix="/api/scenarios/smart-ev-cockpit")


@router.get("/identities")
def identities(request: Request) -> dict:
    service = request.app.state.container.identity_service
    return {
        "identities": [
            identity.model_dump(mode="json")
            for identity in service.list_identities()
        ]
    }


@router.put("/identities/{actor_id}")
def update_identity(
    actor_id: str,
    payload: UpdateUserIdentityRequest,
    request: Request,
) -> dict:
    service = request.app.state.container.identity_service
    try:
        identity = service.update_identity(
            actor_id,
            user_id=payload.user_id,
            display_name=payload.display_name,
            profile_note=payload.profile_note,
        )
    except UnknownIdentityError as exc:
        raise HTTPException(status_code=404, detail="Identity not found") from exc
    return {"identity": identity.model_dump(mode="json")}


@router.get("/profiles/{actor_id}")
def profile(actor_id: str, request: Request) -> dict:
    container = request.app.state.container
    try:
        summary = container.identity_service.get_profile(
            actor_id,
            powercontext_client=container.powercontext_client,
        )
    except UnknownIdentityError as exc:
        raise HTTPException(status_code=404, detail="Identity not found") from exc
    except PowerContextConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"profile": summary.model_dump(mode="json")}
