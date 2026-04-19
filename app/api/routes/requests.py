"""
Endpoints versionados /v1/requests*.
"""
import asyncio

from fastapi import APIRouter, HTTPException, status

from api.dependencies import PipelineDep, StoreDep
from models.schemas import (
    IntakeCreate,
    IntakeCreateResponse,
    NotificationStatusResponse,
)

router = APIRouter()


@router.post(
    "/v1/requests",
    response_model=IntakeCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_request(
    body: IntakeCreate,
    store: StoreDep,
) -> IntakeCreateResponse:
    """Registra la intención del usuario (queued); no contacta al proveedor."""
    req_id = await store.create_intake(body.user_input)
    return IntakeCreateResponse(id=req_id)


@router.post(
    "/v1/requests/{req_id}/process",
    status_code=status.HTTP_202_ACCEPTED,
)
async def process_request(
    req_id: str,
    store: StoreDep,
    pipeline: PipelineDep,
) -> None:
    """
    Pasa a processing y lanza extracción + entrega (idempotente si sent/processing).
    """
    outcome, user_input = await store.try_begin_pipeline(req_id)
    if outcome == "missing":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )
    if outcome == "noop":
        return None
    assert user_input is not None
    asyncio.create_task(pipeline.run(req_id, user_input))
    return None


@router.get(
    "/v1/requests/{req_id}",
    response_model=NotificationStatusResponse,
)
async def get_request(
    req_id: str,
    store: StoreDep,
) -> NotificationStatusResponse:
    """
    Devuelve el estado actual de la solicitud.
    """
    st = await store.get_status(req_id)
    if st is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )
    return NotificationStatusResponse(id=req_id, status=st)
