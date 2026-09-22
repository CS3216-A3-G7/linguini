"""Provider schemas must express requirements before a paid generation happens."""

import json

import httpx
import pytest
from openai import OpenAI
from openai.lib._pydantic import to_strict_json_schema
from pydantic import ValidationError

from app.services.learning_tasks import scene_generation_response_model
from app.services.openai_learning_tasks import OpenAILearningTaskGenerator
from tests.test_openai_learning_tasks import INPUT, tasks


@pytest.mark.parametrize("focus", ["sceneDescription", "chainedDescription"])
def test_provider_schema_requires_nonnullable_english_translation(focus):
    model = scene_generation_response_model(INPUT)
    schema = to_strict_json_schema(model)
    task_ref = schema["properties"][focus]["$ref"].split("/")[-1]
    task = schema["$defs"][task_ref]
    question_ref = task["properties"]["questions"]["items"]["$ref"].split("/")[-1]
    question = schema["$defs"][question_ref]
    assert "translation" in question["required"]
    assert question["properties"]["translation"]["type"] == "string"
    assert question["properties"]["translation"]["minLength"] == 1


@pytest.mark.parametrize("focus", ["sceneDescription", "chainedDescription"])
@pytest.mark.parametrize("translation", [None, "", "   "])
def test_description_cannot_parse_without_usable_translation(focus, translation):
    model = scene_generation_response_model(INPUT)
    payload = {task["focus"]: task for task in tasks()["tasks"]}
    payload[focus]["questions"][0]["translation"] = translation
    with pytest.raises(ValidationError):
        model.model_validate(payload)


@pytest.mark.parametrize("focus", [
    "genderNumberAgreement", "pluralNounForm", "sceneDescription", "chainedDescription"
])
def test_empty_scene_references_are_forbidden_in_provider_schema(focus):
    model = scene_generation_response_model(INPUT)
    schema = to_strict_json_schema(model)
    task = schema["$defs"][schema["properties"][focus]["$ref"].split("/")[-1]]
    question = schema["$defs"][
        task["properties"]["questions"]["items"]["$ref"].split("/")[-1]
    ]
    assert question["properties"]["objectKeys"]["minItems"] == 1
    assert question["properties"]["objectKeys"]["items"]["enum"] == ["object_1", "object_2"]
    payload = {task["focus"]: task for task in tasks()["tasks"]}
    payload[focus]["questions"][0]["objectKeys"] = []
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_schema_rejects_ids_from_another_scene():
    model = scene_generation_response_model(INPUT)
    payload = {task["focus"]: task for task in tasks()["tasks"]}
    payload["genderNumberAgreement"]["questions"][0]["objectKeys"] = ["unrelated-object"]
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_real_sdk_parsing_preserves_translations_through_provider(tmp_path):
    """Exercise SDK serialization/parsing and our normalization without network/credits."""
    calls = []
    lesson = {task["focus"]: task for task in tasks()["tasks"]}

    def respond(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "resp_test", "object": "response", "created_at": 0,
            "status": "completed", "model": "test-model", "error": None,
            "incomplete_details": None, "instructions": None,
            "parallel_tool_calls": False, "tool_choice": "auto", "tools": [],
            "output": [{
                "id": "msg_test", "type": "message", "role": "assistant",
                "status": "completed", "content": [{
                    "type": "output_text", "text": json.dumps(lesson), "annotations": [],
                }],
            }],
        })

    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Generate lessons.")
    with OpenAI(
        api_key="not-a-real-key",
        http_client=httpx.Client(transport=httpx.MockTransport(respond)),
    ) as client:
        provider = OpenAILearningTaskGenerator(
            "not-a-real-key", "test-model", client=client, prompt_path=prompt,
        )
        result = provider.generate(INPUT)

    assert len(calls) == 1
    sent_format = calls[0]["text"]["format"]
    assert sent_format["strict"] is True
    assert sent_format["schema"] == to_strict_json_schema(scene_generation_response_model(INPUT))
    assert result.tasks[2].questions[0].translation == "The cup is red."
    assert result.tasks[3].questions[0].translation == "The red cup is on the table."
    assert result.tasks[3].questions[0].token_bank
