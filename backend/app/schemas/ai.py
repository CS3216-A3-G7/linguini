"""AI-call observability schemas."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from app.schemas.base import EntityModel, NonEmptyText
from app.schemas.enums import AiFeature, AiRunStatus


class AiGenerationRun(EntityModel):
    user_id: UUID | None = None
    session_id: UUID | None = None
    journal_id: UUID | None = None
    feature: AiFeature
    model_name: NonEmptyText
    prompt_version: NonEmptyText
    schema_version: NonEmptyText
    status: AiRunStatus = AiRunStatus.PENDING
    latency_ms: Annotated[int, Field(ge=0)] | None = None
    input_tokens: Annotated[int, Field(ge=0)] | None = None
    output_tokens: Annotated[int, Field(ge=0)] | None = None
    validation_passed: bool | None = None
    error_code: Annotated[str, Field(max_length=100)] | None = None
    input_reference: str | None = None
    output_reference: str | None = None
    completed_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_ai_run(self) -> AiGenerationRun:
        if self.status in {AiRunStatus.SUCCEEDED, AiRunStatus.FAILED}:
            if self.completed_at is None:
                raise ValueError("terminal AI runs require completedAt")
        if self.status is AiRunStatus.FAILED and self.error_code is None:
            raise ValueError("failed AI runs require errorCode")
        return self
