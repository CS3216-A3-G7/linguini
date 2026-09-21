from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.schemas.learning_tasks import LearningTaskResult
from app.services.learning_tasks import LearningTaskGenerationError
from app.services.openai_learning_tasks import OpenAILearningTaskGenerator

INPUT = {
    "targetLanguage": "fr",
    "sceneTitle": "Desk",
    "sceneSummary": "A red cup is on a table.",
    "objects": [{"key": "object_1", "source": "cup", "translation": "tasse"}],
    "attributes": [{"key": "object_1:color", "source": "red", "translation": "rouge"}],
    "relationships": [{"key": "relation_1", "source": "on", "translation": "sur"}],
}


def question(question_id: str, *, object_keys=("object_1",), translation=None):
    return {
        "questionId": question_id,
        "prompt": "La tasse est ___.",
        "options": [
            {"optionId": f"{question_id}-a", "label": "rouge"},
            {"optionId": f"{question_id}-b", "label": "rouges"},
        ],
        "correctOptionId": f"{question_id}-a",
        "translation": translation,
        "objectKeys": list(object_keys),
        "attributeKeys": [],
        "relationshipKeys": [],
    }


def tasks(*, scene_translation="The cup is red."):
    return {
        "tasks": [
            {
                "focus": "genderAgreement",
                "title": "Gender agreement",
                "explanation": "Adjectives match the noun.",
                "questions": [question("gender-1"), question("gender-2")],
            },
            {
                "focus": "singularPlural",
                "title": "Singular and plural",
                "explanation": "Most nouns add -s.",
                "questions": [question("plural-1"), question("plural-2")],
            },
            {
                "focus": "sceneDescription",
                "title": "Describe the scene",
                "explanation": "Build one full sentence.",
                "questions": [
                    question("scene-1", translation=scene_translation),
                    question("scene-2", translation=scene_translation),
                ],
            },
        ]
    }


def generator(tmp_path: Path, result: LearningTaskResult | None):
    prompt = tmp_path / "learning_tasks.txt"
    prompt.write_text("Generate three short learning tasks.", encoding="utf-8")
    client = SimpleNamespace(
        responses=SimpleNamespace(
            parse=MagicMock(return_value=SimpleNamespace(output_parsed=result))
        )
    )
    return OpenAILearningTaskGenerator(
        "test-key", "test-model", client=client, prompt_path=prompt
    ), client


def test_generation_uses_the_shared_structured_contract(tmp_path):
    expected = LearningTaskResult.model_validate(tasks())
    provider, client = generator(tmp_path, expected)

    result = provider.generate(INPUT)

    assert result == expected
    call = client.responses.parse.call_args.kwargs
    assert call["text_format"] is LearningTaskResult
    assert call["model"] == "test-model"


def test_generation_rejects_keys_outside_the_supplied_scene(tmp_path):
    payload = tasks()
    payload["tasks"][0]["questions"][0]["objectKeys"] = ["object_9"]
    provider, _ = generator(tmp_path, LearningTaskResult.model_validate(payload))

    with pytest.raises(LearningTaskGenerationError):
        provider.generate(INPUT)


def test_generation_ignores_an_unknown_relationship_metadata_key(tmp_path):
    payload = tasks()
    payload["tasks"][2]["questions"][0]["relationshipKeys"] = ["on"]
    provider, _ = generator(tmp_path, LearningTaskResult.model_validate(payload))

    result = provider.generate(INPUT)

    assert result.tasks[2].questions[0].relationship_keys == []


def test_generation_requires_a_translated_scene_sentence(tmp_path):
    provider, _ = generator(
        tmp_path, LearningTaskResult.model_validate(tasks(scene_translation=None))
    )

    with pytest.raises(LearningTaskGenerationError):
        provider.generate(INPUT)


def test_generation_rejects_an_empty_response(tmp_path):
    provider, _ = generator(tmp_path, None)

    with pytest.raises(LearningTaskGenerationError):
        provider.generate(INPUT)
