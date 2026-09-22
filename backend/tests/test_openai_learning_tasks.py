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


def question(
    question_id: str,
    *,
    object_keys=("object_1",),
    relationship_keys=(),
    translation=None,
):
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
        "relationshipKeys": list(relationship_keys),
    }


def tasks(*, scene_translation="The cup is red."):
    return {
        "tasks": [
            {
                "focus": "genderNumberAgreement",
                "title": "Gender and number agreement",
                "explanation": "Adjectives match the noun.",
                "questions": [question("gender-1"), question("gender-2")],
            },
            {
                "focus": "prepositionRelation",
                "title": "Prepositions in the scene",
                "explanation": "Use the relationship shown in the scene.",
                "questions": [
                    question("relation-1", relationship_keys=("relation_1",)),
                    question("relation-2", relationship_keys=("relation_1",)),
                ],
            },
            {
                "focus": "sceneDescription",
                "title": "Describe the scene",
                "explanation": "Build one full sentence.",
                "questions": [
                    question(
                        "scene-1",
                        relationship_keys=("relation_1",),
                        translation=scene_translation,
                    ),
                    question(
                        "scene-2",
                        relationship_keys=("relation_1",),
                        translation=scene_translation,
                    ),
                ],
            },
        ]
    }


def generator(tmp_path: Path, result: LearningTaskResult | None):
    prompt = tmp_path / "learning_tasks.txt"
    prompt.write_text("Generate learning tasks.", encoding="utf-8")
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
    payload["tasks"][0]["questions"][0]["relationshipKeys"] = ["on"]
    provider, _ = generator(tmp_path, LearningTaskResult.model_validate(payload))

    result = provider.generate(INPUT)

    assert result.tasks[0].questions[0].relationship_keys == []


def test_generation_requires_a_relationship_for_relation_tasks(tmp_path):
    payload = tasks()
    payload["tasks"][1]["questions"][0]["relationshipKeys"] = []
    provider, _ = generator(tmp_path, LearningTaskResult.model_validate(payload))

    with pytest.raises(LearningTaskGenerationError):
        provider.generate(INPUT)


def test_generation_requires_chained_descriptions_for_two_relationships(tmp_path):
    payload = tasks()
    two_relation_input = {
        **INPUT,
        "relationships": [
            *INPUT["relationships"],
            {"key": "relation_2", "source": "next_to", "translation": "à côté de"},
        ],
    }
    provider, _ = generator(tmp_path, LearningTaskResult.model_validate(payload))

    with pytest.raises(LearningTaskGenerationError):
        provider.generate(two_relation_input)


def test_generation_allows_only_an_agreement_task_without_relationships(tmp_path):
    payload = tasks()
    payload["tasks"] = payload["tasks"][:1]
    no_relation_input = {**INPUT, "relationships": []}
    provider, _ = generator(tmp_path, LearningTaskResult.model_validate(payload))

    assert provider.generate(no_relation_input).tasks[0].focus == "genderNumberAgreement"


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
