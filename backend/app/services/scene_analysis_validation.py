"""Validation for raw scene-analysis model output."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import ValidationError

from app.schemas.enums import SYMMETRIC_SCENE_RELATION_TYPES, SceneRelationType
from app.schemas.scene_analysis import (
    SceneAnalysisIssue,
    SceneAnalysisIssueCode,
    SceneAnalysisModelResult,
)
from app.services.scene_analysis import SceneAnalysisError


class SceneAnalysisValidationError(SceneAnalysisError):
    def __init__(self, issues: Sequence[SceneAnalysisIssue]) -> None:
        self.issues = tuple(issues)
        summary = "; ".join(
            f"{issue.code.value}: {issue.message}" for issue in self.issues
        )
        super().__init__(summary)


def _error_path(location: tuple[Any, ...]) -> str:
    path = ""
    for part in location:
        if isinstance(part, int):
            path += f"[{part}]"
        elif path:
            path += f".{part}"
        else:
            path = str(part)
    return path


def _issue(
    code: SceneAnalysisIssueCode, message: str, path: str | None = None
) -> SceneAnalysisIssue:
    return SceneAnalysisIssue(code=code, message=message, path=path)


def validate_scene_analysis(result: SceneAnalysisModelResult) -> SceneAnalysisModelResult:
    issues: list[SceneAnalysisIssue] = []

    object_keys: set[str] = set()
    for index, scene_object in enumerate(result.objects):
        if scene_object.key in object_keys:
            issues.append(
                _issue(
                    SceneAnalysisIssueCode.DUPLICATE_OBJECT_KEY,
                    f"duplicate object key {scene_object.key!r}",
                    f"objects[{index}].key",
                )
            )
        object_keys.add(scene_object.key)

    relation_keys: set[str] = set()
    for index, relation in enumerate(result.relations):
        if relation.key in relation_keys:
            issues.append(
                _issue(
                    SceneAnalysisIssueCode.DUPLICATE_RELATION_KEY,
                    f"duplicate relation key {relation.key!r}",
                    f"relations[{index}].key",
                )
            )
        relation_keys.add(relation.key)

    box_fields = ("x", "y", "width", "height")
    for index, scene_object in enumerate(result.objects):
        box = scene_object.bounding_box
        non_finite = [
            field for field in box_fields if not math.isfinite(getattr(box, field))
        ]
        if non_finite:
            for field in non_finite:
                value = getattr(box, field)
                issues.append(
                    _issue(
                        SceneAnalysisIssueCode.NON_FINITE_BOUNDING_BOX,
                        f"object {scene_object.key!r} has non-finite {field}={value!r}",
                        f"objects[{index}].boundingBox.{field}",
                    )
                )
            continue

        for field in box_fields:
            value = getattr(box, field)
            if not 0 <= value <= 1:
                issues.append(
                    _issue(
                        SceneAnalysisIssueCode.BOUNDING_BOX_OUT_OF_RANGE,
                        f"object {scene_object.key!r} has {field}={value!r}, expected 0..1",
                        f"objects[{index}].boundingBox.{field}",
                    )
                )

        for field in ("width", "height"):
            value = getattr(box, field)
            if value <= 0:
                issues.append(
                    _issue(
                        SceneAnalysisIssueCode.NON_POSITIVE_BOUNDING_BOX_SIZE,
                        f"object {scene_object.key!r} has non-positive {field}={value!r}",
                        f"objects[{index}].boundingBox.{field}",
                    )
                )

        if box.x + box.width > 1 + 1e-9:
            issues.append(
                _issue(
                    SceneAnalysisIssueCode.BOUNDING_BOX_OUTSIDE_IMAGE,
                    f"object {scene_object.key!r} has x + width={box.x + box.width!r}",
                    f"objects[{index}].boundingBox",
                )
            )
        if box.y + box.height > 1 + 1e-9:
            issues.append(
                _issue(
                    SceneAnalysisIssueCode.BOUNDING_BOX_OUTSIDE_IMAGE,
                    f"object {scene_object.key!r} has y + height={box.y + box.height!r}",
                    f"objects[{index}].boundingBox",
                )
            )

    seen_relations: set[tuple[SceneRelationType, str, str]] = set()
    for index, relation in enumerate(result.relations):
        relation_path = f"relations[{index}]"
        if relation.source_object_key not in object_keys:
            issues.append(
                _issue(
                    SceneAnalysisIssueCode.UNKNOWN_RELATION_OBJECT,
                    f"relation {relation.key!r} has unknown source object key "
                    f"{relation.source_object_key!r}",
                    f"{relation_path}.sourceObjectKey",
                )
            )
        if relation.target_object_key not in object_keys:
            issues.append(
                _issue(
                    SceneAnalysisIssueCode.UNKNOWN_RELATION_OBJECT,
                    f"relation {relation.key!r} has unknown target object key "
                    f"{relation.target_object_key!r}",
                    f"{relation_path}.targetObjectKey",
                )
            )

        is_self_relation = relation.source_object_key == relation.target_object_key
        if is_self_relation:
            issues.append(
                _issue(
                    SceneAnalysisIssueCode.SELF_RELATION,
                    f"relation {relation.key!r} connects object "
                    f"{relation.source_object_key!r} to itself",
                    relation_path,
                )
            )
            continue

        relation_tuple = (
            relation.relation_type,
            relation.source_object_key,
            relation.target_object_key,
        )
        if relation_tuple in seen_relations:
            issues.append(
                _issue(
                    SceneAnalysisIssueCode.DUPLICATE_RELATION,
                    f"relation {relation.key!r} duplicates "
                    f"{relation.relation_type.value} {relation.source_object_key!r}"
                    f"->{relation.target_object_key!r}",
                    relation_path,
                )
            )
        elif (
            relation.relation_type in SYMMETRIC_SCENE_RELATION_TYPES
            and (
                relation.relation_type,
                relation.target_object_key,
                relation.source_object_key,
            )
            in seen_relations
        ):
            issues.append(
                _issue(
                    SceneAnalysisIssueCode.SYMMETRIC_DUPLICATE_RELATION,
                    f"relation {relation.key!r} reverses an earlier "
                    f"{relation.relation_type.value} relation",
                    relation_path,
                )
            )
        seen_relations.add(relation_tuple)

    if issues:
        raise SceneAnalysisValidationError(issues)
    return result


def parse_scene_analysis(payload: Mapping[str, Any] | str | bytes) -> SceneAnalysisModelResult:
    try:
        if isinstance(payload, (str, bytes)):
            result = SceneAnalysisModelResult.model_validate_json(payload)
        else:
            result = SceneAnalysisModelResult.model_validate(payload)
    except ValidationError as exc:
        issues = [
            _issue(
                SceneAnalysisIssueCode.INVALID_SCHEMA,
                error["msg"],
                _error_path(error["loc"]),
            )
            for error in exc.errors()
        ]
        raise SceneAnalysisValidationError(issues) from exc
    return validate_scene_analysis(result)
