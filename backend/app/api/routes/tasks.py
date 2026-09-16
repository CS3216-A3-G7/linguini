from uuid import UUID

from fastapi import APIRouter

from app.api.errors import service_not_implemented
from app.schemas.tasks import (
    SessionTaskPublic,
    SkipTaskRequest,
    SubmitTaskAttemptRequest,
    TaskActionResponse,
    TaskHint,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=SessionTaskPublic)
async def get_task(task_id: UUID) -> SessionTaskPublic:
    service_not_implemented("Get task")


@router.post("/{task_id}/start", response_model=TaskActionResponse)
async def start_task(task_id: UUID) -> TaskActionResponse:
    service_not_implemented("Start task")


@router.post("/{task_id}/attempts", response_model=TaskActionResponse)
async def submit_task_attempt(
    task_id: UUID, request: SubmitTaskAttemptRequest
) -> TaskActionResponse:
    service_not_implemented("Evaluate task attempt")


@router.post("/{task_id}/hints", response_model=TaskHint)
async def request_task_hint(task_id: UUID) -> TaskHint:
    service_not_implemented("Request task hint")


@router.post("/{task_id}/complete", response_model=TaskActionResponse)
async def complete_task(task_id: UUID) -> TaskActionResponse:
    service_not_implemented("Complete task")


@router.post("/{task_id}/skip", response_model=TaskActionResponse)
async def skip_task(task_id: UUID, request: SkipTaskRequest) -> TaskActionResponse:
    service_not_implemented("Skip task")
