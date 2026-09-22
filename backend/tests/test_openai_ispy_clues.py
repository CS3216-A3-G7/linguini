import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.repositories.postgres.workflow import _ispy_clue_payload
from app.schemas.media import SceneObject
from app.schemas.translation import SceneTranslationResult
from app.services.ispy_clues import ISpyClueGenerationError, scene_clue_response_model
from app.services.openai_ispy_clues import OpenAIISpyClueGenerator

INPUT = {
    "targetLanguage": "es",
    "sceneTitle": "Desk",
    "sceneSummary": "A red cup is on a table.",
    "objects": [
        {
            "key": "object_1", "source": "cup", "translation": "taza",
            "anchorPoint": {"x": 0.2, "y": 0.3},
        },
        {
            "key": "object_2", "source": "table", "translation": "mesa",
            "anchorPoint": {"x": 0.5, "y": 0.7},
        },
    ],
    "attributes": [{
        "key": "object_1:color", "objectKey": "object_1", "source": "red", "translation": "roja",
    }],
    "relationships": [{
        "key": "relation_1", "source": "on", "translation": "sobre",
        "subjectObjectKey": "object_1", "referenceObjectKey": "object_2",
    }],
}


def clues():
    return {"clues": [
        {
            "clue": "es roja y está a la izquierda", "answerObjectKey": "object_1",
            "objectKeys": ["object_1"], "relationshipKeys": [],
        },
        {
            "clue": "está debajo de algo rojo", "answerObjectKey": "object_2",
            "objectKeys": ["object_2"], "relationshipKeys": ["relation_1"],
        },
    ]}


def generator(tmp_path: Path, data):
    prompt = tmp_path / "i_spy_clues.txt"
    prompt.write_text("Generate clue endings.", encoding="utf-8")

    def parse(**kwargs):
        return SimpleNamespace(output_parsed=kwargs["text_format"].model_validate(data))

    client = SimpleNamespace(responses=SimpleNamespace(parse=MagicMock(side_effect=parse)))
    return (
        OpenAIISpyClueGenerator("test-key", "test-model", client=client, prompt_path=prompt),
        client,
    )


def test_generation_returns_only_scene_grounded_clue_endings(tmp_path):
    provider, client = generator(tmp_path, clues())

    result = provider.generate(INPUT)

    assert [clue.clue for clue in result.clues] == [
        "es roja y está a la izquierda", "está debajo de algo rojo"
    ]
    assert [clue.answer_object_key for clue in result.clues] == ["object_1", "object_2"]
    call = client.responses.parse.call_args.kwargs
    assert json.loads(call["input"]) == INPUT
    assert "image" not in call["input"].casefold()


def test_schema_rejects_answer_keys_from_another_scene():
    data = clues()
    data["clues"][0]["answerObjectKey"] = "outside-scene"
    with pytest.raises(ValidationError):
        scene_clue_response_model(INPUT).model_validate(data)


def test_generation_rejects_a_repeated_i_spy_opening(tmp_path):
    data = clues()
    data["clues"][0]["clue"] = "I spy with my little eye, something that is red"
    provider, _ = generator(tmp_path, data)
    with pytest.raises(ISpyClueGenerationError):
        provider.generate(INPUT)


def test_clue_payload_converts_a_pydantic_bounding_box_to_an_anchor_point():
    object_id = uuid4()
    scene = SceneTranslationResult.model_validate({
        "objects": [{"key": str(object_id), "source": "cup", "translation": "taza"}],
        "attributes": [], "relationships": [],
    })
    payload = _ispy_clue_payload(
        {"targetLanguage": "es", "sceneTitle": "Desk", "sceneSummary": "A cup."},
        scene,
        [SceneObject(
            id=object_id, session_id=uuid4(), label="cup",
            bounding_box={"x": 0.2, "y": 0.3, "width": 0.2, "height": 0.4},
        )],
    )

    assert payload["objects"][0]["anchorPoint"] == {"x": 0.3, "y": 0.5}
