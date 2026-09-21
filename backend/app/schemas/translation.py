"""Structured scene-vocabulary translation contracts."""

from typing import Annotated

from pydantic import Field

from app.schemas.base import ApiModel, NonEmptyText


class TranslatedTerm(ApiModel):
    key: NonEmptyText
    source: NonEmptyText
    translation: Annotated[str, Field(min_length=1, max_length=300)]
    article: Annotated[str, Field(min_length=1, max_length=20)] | None = None
    gender: Annotated[str, Field(pattern="^(masculine|feminine)$")] | None = None


class SceneTranslationResult(ApiModel):
    objects: list[TranslatedTerm]
    attributes: list[TranslatedTerm]
    relationships: list[TranslatedTerm]
