"""Structured contracts for generated grammar learning tasks."""

from typing import Annotated, Literal

from pydantic import Field

from app.schemas.base import ApiModel, NonEmptyText

type LearningTaskFocus = Literal[
    "genderNumberAgreement",
    "prepositionRelation",
    "sceneDescription",
    "chainedDescription",
]

REQUIRED_TASK_FOCUS_ORDER: tuple[str, ...] = (
    "genderNumberAgreement",
    "prepositionRelation",
    "sceneDescription",
    "chainedDescription",
)


class GeneratedChoice(ApiModel):
    option_id: NonEmptyText
    label: NonEmptyText


class GeneratedQuestion(ApiModel):
    question_id: NonEmptyText
    prompt: NonEmptyText
    options: Annotated[list[GeneratedChoice], Field(min_length=2)]
    correct_option_id: NonEmptyText
    translation: str | None = None
    object_keys: list[str] = Field(default_factory=list)
    attribute_keys: list[str] = Field(default_factory=list)
    relationship_keys: list[str] = Field(default_factory=list)


class GeneratedLearningTask(ApiModel):
    focus: LearningTaskFocus
    title: NonEmptyText
    explanation: NonEmptyText
    questions: Annotated[list[GeneratedQuestion], Field(min_length=2, max_length=4)]


class LearningTaskResult(ApiModel):
    tasks: Annotated[
        list[GeneratedLearningTask],
        Field(min_length=1, max_length=len(REQUIRED_TASK_FOCUS_ORDER)),
    ]
