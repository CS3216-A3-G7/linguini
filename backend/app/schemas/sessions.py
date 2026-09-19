"""Learning-session workflow schemas."""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from app.schemas.base import ApiModel, EntityModel
from app.schemas.enums import SessionStatus
from app.schemas.media import SceneObject
from app.schemas.tasks import SessionProgress, SessionTaskPublic


class Session(EntityModel):
    user_id: UUID
    language_profile_id: UUID
    scene_media_asset_id: UUID
    status: SessionStatus = SessionStatus.CREATED
    started_at: AwareDatetime | None = None
    completed_at: AwareDatetime | None = None
    abandoned_at: AwareDatetime | None = None
    plan_version: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    failure_code: Annotated[str, Field(max_length=100)] | None = None

    @model_validator(mode="after")
    def validate_terminal_timestamp(self) -> Session:
        if self.status is SessionStatus.COMPLETED and self.completed_at is None:
            raise ValueError("completed sessions require completedAt")
        if self.status is SessionStatus.ABANDONED and self.abandoned_at is None:
            raise ValueError("abandoned sessions require abandonedAt")
        if self.completed_at is not None and self.abandoned_at is not None:
            raise ValueError("a session cannot be both completed and abandoned")
        return self


class CreateSessionRequest(ApiModel):
    language_profile_id: UUID
    media_asset_id: UUID
    idempotency_key: Annotated[str, Field(min_length=8, max_length=200)] | None = None


class GenerateSessionPlanRequest(ApiModel):
    desired_vocabulary_count: Annotated[int, Field(ge=1, le=20)] = 5
    include_pronunciation: bool = True
    include_grammar: bool = True
    include_syntax: bool = True
    include_sentence_building: bool = True
    ispy_round_count: Annotated[int, Field(ge=1, le=20)] = 5


class SessionDetailResponse(ApiModel):
    analysis_mode: Literal["placeholder"] | None = None
    demo_state: DemoPracticeState | None = None
    session: Session
    scene_objects: list[SceneObject] = Field(default_factory=list)
    tasks: list[SessionTaskPublic] = Field(default_factory=list)
    next_task_id: UUID | None = None
    progress: SessionProgress | None = None


class SessionSummaryResponse(ApiModel):
    session: Session
    progress: SessionProgress
    learned_vocabulary_ids: list[UUID] = Field(default_factory=list)


class DemoPracticeState(ApiModel):
    answers: dict[str, str] = Field(default_factory=dict)
    clues: dict[str, str] = Field(default_factory=dict)
    scene_id: str
    completed_task_ids: list[str] = Field(default_factory=list)
    scored_round_ids: list[str] = Field(default_factory=list)
    analysis_scored: bool = False
    rounds_played: int = 0
    correct_rounds: int = 0
    session_xp: int = 0
    mic_ready: bool = False


class StoredDemoSession(ApiModel):
    session: Session
    state: DemoPracticeState
    idempotency_key: str | None = None


class DemoPracticeEventRequest(ApiModel):
    kind: Literal["analysis", "task", "round", "clue"]
    item_id: str | None = None
    answer_id: str | None = None
    text: Annotated[str, Field(max_length=1000)] | None = None


SessionDetailResponse.model_rebuild()
