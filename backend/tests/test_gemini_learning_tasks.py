import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.gemini_learning_tasks import GeminiLearningTaskGenerator
from app.services.learning_tasks import (
    LearningTaskGenerationError,
    generation_response_model,
    required_task_focuses,
)
from tests.test_openai_learning_tasks import INPUT, tasks


def generator(tmp_path: Path, payload: str):
    if payload:
        payload = json.dumps({task["focus"]: task for task in json.loads(payload)["tasks"]})
    prompt = tmp_path / "learning_tasks.txt"
    prompt.write_text("Generate learning tasks.", encoding="utf-8")
    client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=MagicMock(return_value=SimpleNamespace(text=payload))
        )
    )
    return GeminiLearningTaskGenerator(
        "test-key", "test-model", client=client, prompt_path=prompt
    ), client


def test_generation_returns_the_required_tasks_for_one_relationship(tmp_path):
    provider, client = generator(tmp_path, json.dumps(tasks()))

    result = provider.generate(INPUT)

    assert [task.focus for task in result.tasks] == [
        "genderNumberAgreement",
        "pluralNounForm",
        "sceneDescription",
        "chainedDescription",
    ]
    call = client.models.generate_content.call_args.kwargs
    response_model = generation_response_model(required_task_focuses(INPUT))
    assert call["config"].response_json_schema == response_model.model_json_schema(
        by_alias=True
    )


def test_generation_restores_canonical_order(tmp_path):
    payload = tasks()
    payload["tasks"].reverse()
    provider, _ = generator(tmp_path, json.dumps(payload))

    actual = tuple(task.focus for task in provider.generate(INPUT).tasks)
    assert actual == required_task_focuses(INPUT)


def test_generation_rejects_an_unoffered_correct_option(tmp_path):
    payload = tasks()
    payload["tasks"][1]["questions"][0]["correctOptionId"] = "missing"
    provider, _ = generator(tmp_path, json.dumps(payload))

    with pytest.raises(LearningTaskGenerationError):
        provider.generate(INPUT)


def test_generation_rejects_an_empty_response(tmp_path):
    provider, _ = generator(tmp_path, "")

    with pytest.raises(LearningTaskGenerationError):
        provider.generate(INPUT)
