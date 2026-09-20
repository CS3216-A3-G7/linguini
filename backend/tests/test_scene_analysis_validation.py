import copy
import math

import pytest
from pydantic import ValidationError

from app.schemas.enums import SceneRelationType
from app.schemas.scene_analysis import (
    ModelBoundingBox,
    ModelSceneObject,
    ModelSceneRelation,
    SceneAnalysisIssueCode,
    SceneAnalysisModelResult,
)
from app.services.scene_analysis_validation import (
    SceneAnalysisValidationError,
    parse_scene_analysis,
    validate_scene_analysis,
)


def object_payload(key: str = "chair", **box: float) -> dict:
    return {
        "key": key,
        "label": key,
        "confidence": 0.9,
        "boundingBox": {
            "x": box.get("x", 0.1),
            "y": box.get("y", 0.1),
            "width": box.get("width", 0.2),
            "height": box.get("height", 0.2),
        },
        "attributes": {},
    }


def relation_payload(
    key: str = "near-1",
    relation_type: str = "nextTo",
    source: str = "chair",
    target: str = "table",
) -> dict:
    return {
        "key": key,
        "relationType": relation_type,
        "sourceObjectKey": source,
        "targetObjectKey": target,
        "confidence": 0.8,
    }


def valid_payload() -> dict:
    return {
        "title": "Kitchen",
        "summary": "A chair is next to a table.",
        "objects": [object_payload(), object_payload("table", x=0.4)],
        "relations": [relation_payload()],
    }


def valid_result(
    *,
    objects: list[ModelSceneObject] | None = None,
    relations: list[ModelSceneRelation] | None = None,
) -> SceneAnalysisModelResult:
    return SceneAnalysisModelResult(
        title="Kitchen",
        summary="A chair is next to a table.",
        objects=objects
        or [
            ModelSceneObject(
                key="chair",
                label="chair",
                confidence=0.9,
                bounding_box=ModelBoundingBox(x=0.1, y=0.1, width=0.2, height=0.2),
                attributes={},
            ),
            ModelSceneObject(
                key="table",
                label="table",
                confidence=0.9,
                bounding_box=ModelBoundingBox(x=0.4, y=0.1, width=0.2, height=0.2),
                attributes={},
            ),
        ],
        relations=relations or [],
    )


def model_relation(
    *,
    key: str = "relation-1",
    relation_type: SceneRelationType = SceneRelationType.NEXT_TO,
    source: str = "chair",
    target: str = "table",
) -> ModelSceneRelation:
    return ModelSceneRelation(
        key=key,
        relation_type=relation_type,
        source_object_key=source,
        target_object_key=target,
        confidence=0.8,
    )


def issue_codes(error: SceneAnalysisValidationError) -> set[SceneAnalysisIssueCode]:
    return {issue.code for issue in error.issues}


def test_valid_payload_round_trips_with_camel_case_aliases() -> None:
    parsed = parse_scene_analysis(valid_payload())
    dumped = parsed.model_dump(mode="json")

    assert parse_scene_analysis(dumped) == parsed
    assert "boundingBox" in dumped["objects"][0]
    assert "sourceObjectKey" in dumped["relations"][0]
    assert "relationType" in dumped["relations"][0]


@pytest.mark.parametrize(
    "extra",
    [
        {"unexpected": True},
        {"objects": [{**object_payload(), "unexpected": True}, object_payload("table")]},
        {
            "objects": [
                {
                    **object_payload(),
                    "boundingBox": {**object_payload()["boundingBox"], "unexpected": True},
                },
                object_payload("table"),
            ]
        },
        {
            "objects": [object_payload(), object_payload("table")],
            "relations": [{**relation_payload(), "unexpected": True}],
        },
    ],
)
def test_extra_properties_are_reported_as_invalid_schema(extra: dict) -> None:
    payload = valid_payload()
    payload.update(extra)

    with pytest.raises(SceneAnalysisValidationError) as raised:
        parse_scene_analysis(payload)

    assert issue_codes(raised.value) == {SceneAnalysisIssueCode.INVALID_SCHEMA}
    assert not isinstance(raised.value, ValidationError)


@pytest.mark.parametrize(
    ("section", "value"),
    [("objects", 1.1), ("relations", -0.1)],
)
def test_confidence_is_rejected_at_schema_level(section: str, value: float) -> None:
    payload = valid_payload()
    if section == "objects":
        payload["objects"][0]["confidence"] = value
    else:
        payload["relations"][0]["confidence"] = value

    with pytest.raises(SceneAnalysisValidationError) as raised:
        parse_scene_analysis(payload)

    assert issue_codes(raised.value) == {SceneAnalysisIssueCode.INVALID_SCHEMA}


def test_duplicate_object_key() -> None:
    result = valid_result(
        objects=[
            valid_result().objects[0],
            valid_result().objects[0],
        ]
    )

    with pytest.raises(SceneAnalysisValidationError) as raised:
        validate_scene_analysis(result)

    assert SceneAnalysisIssueCode.DUPLICATE_OBJECT_KEY in issue_codes(raised.value)


def test_duplicate_relation_key() -> None:
    relations = [
        model_relation(key="same", relation_type=SceneRelationType.ABOVE),
        model_relation(key="same", relation_type=SceneRelationType.BELOW),
    ]

    with pytest.raises(SceneAnalysisValidationError) as raised:
        validate_scene_analysis(valid_result(relations=relations))

    assert SceneAnalysisIssueCode.DUPLICATE_RELATION_KEY in issue_codes(raised.value)


def test_non_finite_bounding_box() -> None:
    scene_object = valid_result().objects[0]
    scene_object.bounding_box.x = math.inf

    with pytest.raises(SceneAnalysisValidationError) as raised:
        validate_scene_analysis(valid_result(objects=[scene_object]))

    assert SceneAnalysisIssueCode.NON_FINITE_BOUNDING_BOX in issue_codes(raised.value)


def test_bounding_box_out_of_range() -> None:
    scene_object = valid_result().objects[0]
    scene_object.bounding_box.x = -0.1

    with pytest.raises(SceneAnalysisValidationError) as raised:
        validate_scene_analysis(valid_result(objects=[scene_object]))

    assert SceneAnalysisIssueCode.BOUNDING_BOX_OUT_OF_RANGE in issue_codes(raised.value)


def test_non_positive_bounding_box_size() -> None:
    scene_object = valid_result().objects[0]
    scene_object.bounding_box.width = 0

    with pytest.raises(SceneAnalysisValidationError) as raised:
        validate_scene_analysis(valid_result(objects=[scene_object]))

    assert SceneAnalysisIssueCode.NON_POSITIVE_BOUNDING_BOX_SIZE in issue_codes(raised.value)


def test_bounding_box_outside_image() -> None:
    scene_object = valid_result().objects[0]
    scene_object.bounding_box.x = 0.9
    scene_object.bounding_box.width = 0.2

    with pytest.raises(SceneAnalysisValidationError) as raised:
        validate_scene_analysis(valid_result(objects=[scene_object]))

    assert SceneAnalysisIssueCode.BOUNDING_BOX_OUTSIDE_IMAGE in issue_codes(raised.value)


def test_unknown_relation_object() -> None:
    relation = model_relation(source="missing", target="also-missing")

    with pytest.raises(SceneAnalysisValidationError) as raised:
        validate_scene_analysis(valid_result(relations=[relation]))

    assert SceneAnalysisIssueCode.UNKNOWN_RELATION_OBJECT in issue_codes(raised.value)
    assert len(
        [
            issue
            for issue in raised.value.issues
            if issue.code is SceneAnalysisIssueCode.UNKNOWN_RELATION_OBJECT
        ]
    ) == 2


def test_self_relation() -> None:
    relation = model_relation(source="chair", target="chair")

    with pytest.raises(SceneAnalysisValidationError) as raised:
        validate_scene_analysis(valid_result(relations=[relation]))

    assert SceneAnalysisIssueCode.SELF_RELATION in issue_codes(raised.value)


def test_duplicate_relation() -> None:
    relations = [
        model_relation(key="first", relation_type=SceneRelationType.ABOVE),
        model_relation(key="second", relation_type=SceneRelationType.ABOVE),
    ]

    with pytest.raises(SceneAnalysisValidationError) as raised:
        validate_scene_analysis(valid_result(relations=relations))

    assert SceneAnalysisIssueCode.DUPLICATE_RELATION in issue_codes(raised.value)


def test_symmetric_duplicate_relation_but_not_non_symmetric_reverse() -> None:
    symmetric = [
        model_relation(key="first"),
        model_relation(key="second", source="table", target="chair"),
    ]
    with pytest.raises(SceneAnalysisValidationError) as raised:
        validate_scene_analysis(valid_result(relations=symmetric))
    assert SceneAnalysisIssueCode.SYMMETRIC_DUPLICATE_RELATION in issue_codes(raised.value)

    non_symmetric = [
        model_relation(key="first", relation_type=SceneRelationType.ABOVE),
        model_relation(
            key="second",
            relation_type=SceneRelationType.ABOVE,
            source="table",
            target="chair",
        ),
    ]
    validate_scene_analysis(valid_result(relations=non_symmetric))


def test_validator_collects_violations_across_the_whole_payload() -> None:
    duplicate_object = valid_result().objects[0]
    duplicate_object.bounding_box.x = math.nan
    relations = [
        model_relation(key="same", source="missing"),
        model_relation(key="same", source="chair", target="chair"),
    ]

    with pytest.raises(SceneAnalysisValidationError) as raised:
        validate_scene_analysis(
            valid_result(
                objects=[duplicate_object, duplicate_object],
                relations=relations,
            )
        )

    assert issue_codes(raised.value) >= {
        SceneAnalysisIssueCode.DUPLICATE_OBJECT_KEY,
        SceneAnalysisIssueCode.DUPLICATE_RELATION_KEY,
        SceneAnalysisIssueCode.NON_FINITE_BOUNDING_BOX,
        SceneAnalysisIssueCode.UNKNOWN_RELATION_OBJECT,
        SceneAnalysisIssueCode.SELF_RELATION,
    }


def test_invalid_result_is_rejected_without_repairing_or_mutating_it() -> None:
    result = valid_result()
    result.objects[0].bounding_box.x = 2
    before = copy.deepcopy(result)

    with pytest.raises(SceneAnalysisValidationError):
        validate_scene_analysis(result)

    assert result == before
    assert result.objects[0].bounding_box.x == 2
