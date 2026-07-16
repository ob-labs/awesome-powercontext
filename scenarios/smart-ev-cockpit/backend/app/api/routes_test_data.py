from typing import Annotated, Literal

from fastapi import APIRouter, Body, HTTPException, Request
from pydantic import BaseModel, Field

from app.powermem.client import PowerMemConnectionError
from app.services.test_data_service import DEFAULT_IMPORT_MAX_WORKERS

router = APIRouter(prefix="/api/scenarios/smart-ev-cockpit/test-data")


class GenerateTestDataRequest(BaseModel):
    count: int = Field(default=1200, ge=1, le=10000)
    seed: int = 42
    locale: Literal["en", "zh"] = "en"


class ImportTestDataRequest(BaseModel):
    dataset_id: str
    apply: bool = False
    limit: int | None = Field(default=None, ge=1)
    max_workers: int = Field(default=DEFAULT_IMPORT_MAX_WORKERS, ge=1, le=32)


class DeleteTestDataRequest(BaseModel):
    apply: bool = False


@router.post("/generate")
def generate_test_data(payload: GenerateTestDataRequest, request: Request) -> dict:
    container = request.app.state.container
    status = container.test_data_service.generate_dataset(
        count=payload.count,
        seed=payload.seed,
        locale=payload.locale,
        actor_user_ids=_actor_user_ids(container),
    )
    return status.model_dump()


@router.post("/import")
def import_test_data(payload: ImportTestDataRequest, request: Request) -> dict:
    container = request.app.state.container
    try:
        memory = container.powermem_client.require_memory()
    except PowerMemConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not container.test_data_service.dataset_exists(payload.dataset_id):
        raise HTTPException(status_code=404, detail="Dataset file was not found.")

    status = container.test_data_service.start_import_dataset(
        memory=memory,
        dataset_id=payload.dataset_id,
        apply=payload.apply,
        limit=payload.limit,
        max_workers=payload.max_workers,
        actor_user_ids=_actor_user_ids(container),
    )
    return status.model_dump()


@router.get("/status")
def test_data_status(request: Request) -> dict:
    return request.app.state.container.test_data_service.status().model_dump()


@router.delete("/all")
def clear_all_test_data(
    request: Request,
    payload: Annotated[DeleteTestDataRequest | None, Body()] = None,
) -> dict:
    payload = payload or DeleteTestDataRequest()
    container = request.app.state.container
    try:
        memory = container.powermem_client.require_memory()
    except PowerMemConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    status = container.test_data_service.clear_all_memories(
        memory=memory,
        apply=payload.apply,
    )
    return status.model_dump()


@router.delete("/{dataset_id}")
def delete_test_dataset(
    dataset_id: str,
    request: Request,
    payload: Annotated[DeleteTestDataRequest | None, Body()] = None,
) -> dict:
    payload = payload or DeleteTestDataRequest()
    container = request.app.state.container
    try:
        memory = container.powermem_client.require_memory()
    except PowerMemConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    status = container.test_data_service.delete_dataset(
        memory=memory,
        dataset_id=dataset_id,
        apply=payload.apply,
    )
    return status.model_dump()


def _actor_user_ids(container) -> dict[str, str]:
    return {
        identity.actor_id: identity.user_id
        for identity in container.identity_service.list_identities()
    }
