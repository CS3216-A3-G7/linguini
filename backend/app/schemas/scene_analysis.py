"""Schemas for validating raw scene-analysis model output."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from pydantic import AliasChoices, Field, field_validator

from app.schemas.base import ApiModel, NonEmptyText
from app.schemas.enums import SceneRelationType


class ModelBoundingBox(ApiModel):
    """Normalized box; geometry is enforced by the semantic validator, not here."""

    x: float
    y: float
    width: float
    height: float


class ModelAnchorPoint(ApiModel):
    x: float
    y: float


class ModelSceneObject(ApiModel):
    object_key: NonEmptyText = Field(
        validation_alias=AliasChoices("objectKey", "key"),
        serialization_alias="objectKey",
    )
    label: NonEmptyText
    bounding_box: ModelBoundingBox
    anchor_point: ModelAnchorPoint
    attributes: list[NonEmptyText] | dict[NonEmptyText, NonEmptyText] = []
    confidence_score: Annotated[
        float,
        Field(
            ge=0,
            le=1,
            validation_alias=AliasChoices("confidenceScore", "confidence"),
            serialization_alias="confidenceScore",
        ),
    ]

    @property
    def key(self) -> str:
        return self.object_key

    @property
    def confidence(self) -> float:
        return self.confidence_score


class ModelSceneRelation(ApiModel):
    relation_key: NonEmptyText = Field(
        validation_alias=AliasChoices("relationKey", "key"),
        serialization_alias="relationKey",
    )
    subject_object_key: NonEmptyText = Field(
        validation_alias=AliasChoices("subjectObjectKey", "sourceObjectKey"),
        serialization_alias="subjectObjectKey",
    )
    relation: SceneRelationType = Field(
        validation_alias=AliasChoices("relation", "relationType"),
        serialization_alias="relation",
    )
    reference_object_key: NonEmptyText = Field(
        validation_alias=AliasChoices("referenceObjectKey", "targetObjectKey"),
        serialization_alias="referenceObjectKey",
    )
    confidence_score: Annotated[
        float,
        Field(
            ge=0,
            le=1,
            validation_alias=AliasChoices("confidenceScore", "confidence"),
            serialization_alias="confidenceScore",
        ),
    ] = 1.0

    @field_validator("relation", mode="before")
    @classmethod
    def accept_snake_case_relation(cls, value):
        aliases = {
            "leftOf": "left_of",
            "rightOf": "right_of",
            "inFrontOf": "in_front_of",
            "nextTo": "next_to",
        }
        return aliases.get(value, value)

    @property
    def key(self) -> str:
        return self.relation_key

    @property
    def relation_type(self) -> SceneRelationType:
        return self.relation

    @property
    def source_object_key(self) -> str:
        return self.subject_object_key

    @property
    def target_object_key(self) -> str:
        return self.reference_object_key

    @property
    def confidence(self) -> float:
        return self.confidence_score


class SceneAnalysisModelResult(ApiModel):
    suggested_scene_title: NonEmptyText = Field(
        validation_alias=AliasChoices("suggestedSceneTitle", "title"),
        serialization_alias="suggestedSceneTitle",
    )
    summary: NonEmptyText = "A scene containing useful vocabulary."
    objects: Annotated[list[ModelSceneObject], Field(max_length=6)]
    relations: list[ModelSceneRelation] = []

    @property
    def title(self) -> str:
        return self.suggested_scene_title


class SceneAnalysisIssueCode(StrEnum):
    INVALID_SCHEMA = "invalidSchema"
    DUPLICATE_OBJECT_KEY = "duplicateObjectKey"
    DUPLICATE_RELATION_KEY = "duplicateRelationKey"
    NON_FINITE_BOUNDING_BOX = "nonFiniteBoundingBox"
    BOUNDING_BOX_OUT_OF_RANGE = "boundingBoxOutOfRange"
    NON_POSITIVE_BOUNDING_BOX_SIZE = "nonPositiveBoundingBoxSize"
    BOUNDING_BOX_OUTSIDE_IMAGE = "boundingBoxOutsideImage"
    UNKNOWN_RELATION_OBJECT = "unknownRelationObject"
    SELF_RELATION = "selfRelation"
    DUPLICATE_RELATION = "duplicateRelation"
    SYMMETRIC_DUPLICATE_RELATION = "symmetricDuplicateRelation"


@dataclass(frozen=True)
class SceneAnalysisIssue:
    code: SceneAnalysisIssueCode
    message: str
    path: str | None = None
