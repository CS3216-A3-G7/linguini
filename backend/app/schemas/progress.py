"""Read models for the demo progress screen."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.base import ApiModel
from app.schemas.sessions import StoredDemoSession


class ScenarioProgress(ApiModel):
    scene_id: str
    status: Literal["in-progress", "completed", "mastered"]
    spoken_items: Annotated[int, Field(ge=0)]
    total_items: Annotated[int, Field(gt=0)]
    level: str

    @model_validator(mode="after")
    def validate_counts(self) -> "ScenarioProgress":
        if self.spoken_items > self.total_items:
            raise ValueError("spoken items cannot exceed total items")
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
    practice_sessions: list[StoredDemoSession] = Field(default_factory=list)
    language_code: str = "es"
    user_id: UUID
