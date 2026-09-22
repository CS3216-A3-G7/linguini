"""Structured output returned for Linguini's Phase 1 I-Spy clues."""

from typing import Annotated

from pydantic import Field

from app.schemas.base import ApiModel, NonEmptyText


class GeneratedISpyClue(ApiModel):
    """One clue ending and its private scene-object answer."""

    clue: NonEmptyText = Field(
        description="Only the phrase completing 'I spy with my little eye, something that …'."
    )
    answer_object_key: NonEmptyText
    object_keys: Annotated[list[NonEmptyText], Field(min_length=1, max_length=1)]
    relationship_keys: list[NonEmptyText] = Field(default_factory=list)


class ISpyClueResult(ApiModel):
    clues: Annotated[list[GeneratedISpyClue], Field(min_length=1, max_length=2)]
