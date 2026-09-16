from uuid import UUID

from fastapi import APIRouter, status

from app.api.errors import service_not_implemented
from app.schemas.media import ReviewSceneObjectsRequest
from app.schemas.sessions import (
    CreateSessionRequest,
    GenerateSessionPlanRequest,
    Session,
    SessionDetailResponse,
    SessionSummaryResponse,
)
from app.schemas.tasks import SessionTaskPublic

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post(
    "",
    response_model=SessionDetailResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_session(request: CreateSessionRequest) -> SessionDetailResponse:
    service_not_implemented("Create and analyze session")


@router.get("/active", response_model=SessionDetailResponse | None)
async def get_active_session() -> SessionDetailResponse | None:
    service_not_implemented("Get active session")


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: UUID) -> SessionDetailResponse:
    service_not_implemented("Get session")


@router.patch("/{session_id}/scene-objects", response_model=SessionDetailResponse)
async def review_scene_objects(
    session_id: UUID, request: ReviewSceneObjectsRequest
) -> SessionDetailResponse:
    service_not_implemented("Review scene objects")


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
async def list_session_tasks(session_id: UUID) -> list[SessionTaskPublic]:
    service_not_implemented("List session tasks")


@router.get("/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary(session_id: UUID) -> SessionSummaryResponse:
    service_not_implemented("Get session summary")


@router.post("/{session_id}/complete", response_model=Session)
async def complete_session(session_id: UUID) -> Session:
    service_not_implemented("Complete session")


@router.post("/{session_id}/abandon", response_model=Session)
async def abandon_session(session_id: UUID) -> Session:
    service_not_implemented("Abandon session")
