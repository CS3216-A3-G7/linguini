"""Aggregated home-screen response schema."""

from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.schemas.base import ApiModel
from app.schemas.enums import SessionStatus
from app.schemas.journals import Journal
from app.schemas.sessions import Session


class DailyHomeProgress(ApiModel):
    completed_task_count: Annotated[int, Field(ge=0)] = 0
    skipped_task_count: Annotated[int, Field(ge=0)] = 0
    learned_word_count: Annotated[int, Field(ge=0)] = 0


class HomeResponse(ApiModel):
    active_session: Session | None = None
    today_journal: Journal | None = None
    daily_progress: DailyHomeProgress = Field(default_factory=DailyHomeProgress)


class HomeActiveSession(ApiModel):
    id: UUID
    status: SessionStatus
    title: str
    media_asset_id: UUID
    image_url: str | None = None
    completed_task_count: Annotated[int, Field(ge=0)] = 0
    total_task_count: Annotated[int, Field(ge=0)] = 0


class HomeSummaryResponse(ApiModel):
    xp: Annotated[int, Field(ge=0)] = 0
    vocabulary_count: Annotated[int, Field(ge=0)] = 0
    active_session: HomeActiveSession | None = None
