"""Read models for the demo progress screen."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.base import ApiModel


class ScenarioProgress(ApiModel):
    scene_id: str
    session_id: UUID
    media_asset_id: UUID
    title: str
    status: Literal["in-progress", "completed", "mastered"]
    completed_task_count: Annotated[int, Field(ge=0)]
    total_task_count: Annotated[int, Field(gt=0)]
    level: str

    @model_validator(mode="after")
    def validate_counts(self) -> "ScenarioProgress":
        if self.completed_task_count > self.total_task_count:
            raise ValueError("completed tasks cannot exceed total tasks")
        return self


class LeaderboardRow(ApiModel):
    rank: Annotated[int, Field(ge=1)]
    name: str
    xp: Annotated[int, Field(ge=0)]
    is_you: bool = False


class ProgressResponse(ApiModel):
    xp: Annotated[int, Field(ge=0)]
    scenarios: list[ScenarioProgress]
    leaderboard: list[LeaderboardRow]


class StoredProgress(ProgressResponse):
    language_code: str = "es"
    user_id: UUID
