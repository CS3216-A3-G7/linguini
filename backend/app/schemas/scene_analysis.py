"""Schemas for validating raw scene-analysis model output."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from pydantic import Field

from app.schemas.base import ApiModel, NonEmptyText
from app.schemas.enums import SceneRelationType


class ModelBoundingBox(ApiModel):
    """Normalized box; geometry is enforced by the semantic validator, not here."""

    x: float
    y: float
    width: float
    height: float


class ModelSceneObject(ApiModel):
    object_key: NonEmptyText
    label: NonEmptyText
    bounding_box: ModelBoundingBox
    attributes: list[NonEmptyText] = []
    confidence_score: Annotated[float, Field(ge=0, le=1)]


class ModelSceneRelation(ApiModel):
    relation_key: NonEmptyText
    subject_object_key: NonEmptyText
    relation: SceneRelationType
    reference_object_key: NonEmptyText


class SceneAnalysisModelResult(ApiModel):
    suggested_scene_title: NonEmptyText
    objects: list[ModelSceneObject]
    relations: list[ModelSceneRelation] = []


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
