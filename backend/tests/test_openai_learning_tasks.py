from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.schemas.learning_tasks import LearningTaskResult
from app.services.learning_tasks import (
    LearningTaskGenerationError,
    normalize_learning_task_references,
)
from app.services.openai_learning_tasks import OpenAILearningTaskGenerator

INPUT = {
    "targetLanguage": "fr",
    "sceneTitle": "Desk",
    "sceneSummary": "A red cup is on a table.",
    "objects": [
        {"key": "object_1", "source": "cup", "translation": "tasse"},
        {"key": "object_2", "source": "table", "translation": "table"},
    ],
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
            {"optionId": f"{question_id}-c", "label": "roux"},
            {"optionId": f"{question_id}-d", "label": "rousses"},
        ],
        "correctOptionId": f"{question_id}-a",
        "translation": translation,
        "objectKeys": list(object_keys),
        "attributeKeys": [],
        "relationshipKeys": list(relationship_keys),
    }


def builder_question(question_id, relation=True):
    text = "La tasse rouge est sur la table." if relation else "La tasse est rouge."
    return {
        "questionId": question_id,
        "prompt": "Build the French sentence.",
        "interactionType": "sentenceBuilding",
        "correctText": text,
        "tokenBank": text.split(),
        "translation": "The red cup is on the table." if relation else "The cup is red.",
        "objectKeys": ["object_1", "object_2"] if relation else ["object_1"],
        "attributeKeys": ["object_1:color"],
        "relationshipKeys": ["relation_1"] if relation else [],
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
                "focus": "pluralNounForm",
                "title": "Plural nouns",
                "explanation": "Use the plural form of each noun.",
                "questions": [
                    question("plural-1"),
                    question("plural-2"),
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
            {
                "focus": "chainedDescription",
                "title": "Build a sentence",
                "explanation": "Use the colour and location to describe the cup.",
                "questions": [builder_question("build-1"), builder_question("build-2")],
            },
        ]
    }


def tasks_with_chained_description():
    payload = tasks()
    payload["tasks"].pop()
    payload["tasks"].append(
        {
            "focus": "chainedDescription",
            "title": "Describe more of the scene",
            "explanation": "Join the two scene relationships with et.",
            "questions": [
                {
                    "questionId": "chain-1",
                    "prompt": "Build the French sentence.",
                    "interactionType": "sentenceBuilding",
                    "correctText": "La tasse rouge est sur la table et à côté du livre.",
                    "tokenBank": [
                        "La", "tasse", "rouge", "est", "sur", "la", "table",
                        "et", "à", "côté", "du", "livre", ".",
                    ],
                    "translation": "The red cup is on the table and next to the book.",
                    "objectKeys": ["object_1", "object_2", "object_3"],
                    "attributeKeys": ["object_1:color"],
                    "relationshipKeys": ["relation_1", "relation_2"],
                },
                {
                    "questionId": "chain-2",
                    "prompt": "Build another French sentence.",
                    "interactionType": "sentenceBuilding",
                    "correctText": "Le livre est à côté de la table et sous la tasse rouge.",
                    "tokenBank": [
                        "Le", "livre", "est", "à", "côté", "de", "la", "table",
                        "et", "sous", "la", "tasse", "rouge", ".",
                    ],
                    "translation": "The book is next to the table and below the red cup.",
                    "objectKeys": ["object_1", "object_2", "object_3"],
                    "attributeKeys": ["object_1:color"],
                    "relationshipKeys": ["relation_1", "relation_2"],
                },
            ],
        }
    )
    return payload


INPUT_WITH_TWO_RELATIONSHIPS = {
    **INPUT,
    "objects": [
        *INPUT["objects"],
        {"key": "object_3", "source": "book", "translation": "livre"},
    ],
    "relationships": [
        *INPUT["relationships"],
        {"key": "relation_2", "source": "next_to", "translation": "à côté de"},
    ],
}


def generator(tmp_path: Path, result: LearningTaskResult | None):
    prompt = tmp_path / "learning_tasks.txt"
    prompt.write_text("Generate learning tasks.", encoding="utf-8")
    def parse(**kwargs):
        parsed = None if result is None else kwargs["text_format"].model_validate({
            task.focus: task.model_dump() for task in result.tasks
        })
        return SimpleNamespace(output_parsed=parsed)

    client = SimpleNamespace(
        responses=SimpleNamespace(
            parse=MagicMock(side_effect=parse)
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
    assert call["text_format"].model_json_schema()["required"] == [
        "genderNumberAgreement", "pluralNounForm", "sceneDescription", "chainedDescription"
    ]
    assert call["model"] == "test-model"


def test_generation_rejects_keys_outside_the_supplied_scene(tmp_path):
    payload = tasks()
    payload["tasks"][0]["questions"][0]["objectKeys"] = ["object_9"]
    provider, _ = generator(tmp_path, LearningTaskResult.model_validate(payload))

    with pytest.raises(LearningTaskGenerationError):
        provider.generate(INPUT)


def test_generation_repairs_an_unambiguous_relationship_label(tmp_path):
    payload = tasks()
    payload["tasks"][0]["questions"][0]["relationshipKeys"] = ["on"]
    result = normalize_learning_task_references(INPUT, LearningTaskResult.model_validate(payload))

    assert result.tasks[0].questions[0].relationship_keys == ["relation_1"]


def test_description_accepts_extra_valid_relationship_references(tmp_path):
    payload = tasks_with_chained_description()
    payload["tasks"][2]["questions"][0]["relationshipKeys"] = ["relation_1", "relation_2"]
    provider, _ = generator(tmp_path, LearningTaskResult.model_validate(payload))
    assert len(provider.generate(INPUT_WITH_TWO_RELATIONSHIPS).tasks) == 4


def test_description_rejects_ambiguous_relationship_label(tmp_path):
    payload = tasks_with_chained_description()
    payload["tasks"][2]["questions"][0]["relationshipKeys"] = ["on"]
    ambiguous = {**INPUT_WITH_TWO_RELATIONSHIPS, "relationships": [
        {"key": "relation_1", "source": "on", "translation": "sur"},
        {"key": "relation_2", "source": "on", "translation": "sur"},
    ]}
    provider, _ = generator(tmp_path, LearningTaskResult.model_validate(payload))
    with pytest.raises(LearningTaskGenerationError):
        provider.generate(ambiguous)


def test_generation_requires_a_relationship_for_relation_tasks(tmp_path):
    payload = tasks()
    payload["tasks"][2]["questions"][0]["relationshipKeys"] = []
    provider, _ = generator(tmp_path, LearningTaskResult.model_validate(payload))

    with pytest.raises(LearningTaskGenerationError):
        provider.generate(INPUT)


def test_generation_accepts_a_simpler_grounded_builder(tmp_path):
    payload = tasks()
    provider, _ = generator(tmp_path, LearningTaskResult.model_validate(payload))

    assert len(provider.generate(INPUT_WITH_TWO_RELATIONSHIPS).tasks) == 4


def test_generation_accepts_a_chained_sentence_builder(tmp_path):
    provider, _ = generator(
        tmp_path, LearningTaskResult.model_validate(tasks_with_chained_description())
    )

    result = provider.generate(INPUT_WITH_TWO_RELATIONSHIPS)

    question = result.tasks[-1].questions[0]
    assert question.interaction_type == "sentenceBuilding"
    assert question.correct_text == "La tasse rouge est sur la table et à côté du livre."


def test_generation_keeps_sentence_building_without_relationships(tmp_path):
    payload = tasks()
    payload["tasks"] = payload["tasks"][:2] + payload["tasks"][3:]
    payload["tasks"][-1]["questions"] = [
        builder_question("build-1", False), builder_question("build-2", False)
    ]
    no_relation_input = {**INPUT, "relationships": []}
    provider, _ = generator(tmp_path, LearningTaskResult.model_validate(payload))

    assert [task.focus for task in provider.generate(no_relation_input).tasks] == [
        "genderNumberAgreement",
        "pluralNounForm",
        "chainedDescription",
    ]


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


def test_multiple_choice_ignores_misplaced_sentence_builder_fields(tmp_path):
    payload = tasks()
    payload["tasks"][2]["questions"][0].update(
        correctText="La tasse est sur la table.",
        tokenBank=["La", "tasse", "est", "sur", "la", "table", "."],
    )
    provider, _ = generator(tmp_path, LearningTaskResult.model_validate(payload))

    result = provider.generate(INPUT)

    question = result.tasks[2].questions[0]
    assert question.correct_text is None
    assert question.token_bank == []
