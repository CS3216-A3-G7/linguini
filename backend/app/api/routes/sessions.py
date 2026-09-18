from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_practice_service
from app.api.errors import service_not_implemented
from app.schemas.media import ReviewSceneObjectsRequest
from app.schemas.sessions import (
    CreateSessionRequest,
    DemoPracticeEventRequest,
    GenerateSessionPlanRequest,
    Session,
    SessionDetailResponse,
    SessionSummaryResponse,
)
from app.schemas.tasks import SessionTaskPublic
from app.services.practice import PracticeService

router = APIRouter(prefix="/sessions", tags=["sessions"])

PracticeServiceDep = Annotated[PracticeService, Depends(get_practice_service)]


@router.post(
    "",
    response_model=SessionDetailResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_session(
    request: CreateSessionRequest, service: PracticeServiceDep
) -> SessionDetailResponse:
    return service.create(request)


@router.get("/active", response_model=SessionDetailResponse | None)
def get_active_session(service: PracticeServiceDep) -> SessionDetailResponse | None:
    return service.active()


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: UUID, service: PracticeServiceDep) -> SessionDetailResponse:
    return service.get(session_id)


@router.post("/{session_id}/demo-events", response_model=SessionDetailResponse)
def record_demo_event(
    session_id: UUID, request: DemoPracticeEventRequest, service: PracticeServiceDep
) -> SessionDetailResponse:
    return service.record(session_id, request)


@router.patch("/{session_id}/scene-objects", response_model=SessionDetailResponse)
def review_scene_objects(
    session_id: UUID, request: ReviewSceneObjectsRequest, service: PracticeServiceDep
) -> SessionDetailResponse:
    if service.scene_objects is None:
        service_not_implemented("Review scene objects requires PostgreSQL session storage")
    return service.review_objects(session_id, request)


@router.post(
    "/{session_id}/generate-plan",
    response_model=SessionDetailResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_session_plan(
    session_id: UUID, request: GenerateSessionPlanRequest
) -> SessionDetailResponse:
    service_not_implemented("Generate session plan")


@router.get("/{session_id}/tasks", response_model=list[SessionTaskPublic])
def list_session_tasks(session_id: UUID, service: PracticeServiceDep) -> list[SessionTaskPublic]:
    if service.tasks is None:
        service_not_implemented("Task storage requires PostgreSQL session storage")
    return service.get(session_id).tasks


@router.get("/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary(session_id: UUID) -> SessionSummaryResponse:
    service_not_implemented("Get session summary")


@router.post("/{session_id}/complete", response_model=Session)
def complete_session(session_id: UUID, service: PracticeServiceDep) -> Session:
    return service.complete(session_id)


@router.post("/{session_id}/abandon", response_model=Session)
def abandon_session(session_id: UUID, service: PracticeServiceDep) -> Session:
    return service.abandon(session_id)
