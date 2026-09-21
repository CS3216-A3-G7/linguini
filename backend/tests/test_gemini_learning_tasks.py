import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.schemas.learning_tasks import LearningTaskResult
from app.services.gemini_learning_tasks import GeminiLearningTaskGenerator
from app.services.learning_tasks import LearningTaskGenerationError
from tests.test_openai_learning_tasks import INPUT, tasks


def generator(tmp_path: Path, payload: str):
    prompt = tmp_path / "learning_tasks.txt"
    prompt.write_text("Generate three short learning tasks.", encoding="utf-8")
    client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=MagicMock(return_value=SimpleNamespace(text=payload))
        )
    )
    return GeminiLearningTaskGenerator(
        "test-key", "test-model", client=client, prompt_path=prompt
    ), client


def test_generation_returns_the_three_required_tasks(tmp_path):
    provider, client = generator(tmp_path, json.dumps(tasks()))

    result = provider.generate(INPUT)

    assert [task.focus for task in result.tasks] == [
        "genderAgreement",
        "singularPlural",
        "sceneDescription",
    ]
    call = client.models.generate_content.call_args.kwargs
    assert call["config"].response_json_schema == LearningTaskResult.model_json_schema(
        by_alias=True
    )


def test_generation_rejects_tasks_out_of_order(tmp_path):
    payload = tasks()
    payload["tasks"].reverse()
    provider, _ = generator(tmp_path, json.dumps(payload))

    with pytest.raises(LearningTaskGenerationError):
        provider.generate(INPUT)


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
