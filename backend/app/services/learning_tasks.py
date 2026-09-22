"""Provider-neutral grammar learning-task contract and validation."""

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import Field, create_model

from app.schemas.base import ApiModel
from app.schemas.learning_tasks import (
    REQUIRED_TASK_FOCUS_ORDER,
    GeneratedDescriptionQuestion,
    GeneratedLearningTask,
    GeneratedMultipleChoiceQuestion,
    GeneratedSentenceBuilderQuestion,
    LearningTaskResult,
)
from app.services.scene_analysis import SceneAnalysisError

DEFAULT_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "learning_tasks.txt"

KEY_FIELDS = {
    "objects": "object_keys",
    "attributes": "attribute_keys",
    "relationships": "relationship_keys",
}


class LearningTaskGenerationError(SceneAnalysisError):
    """The scene vocabulary could not be turned into usable learning tasks."""


class LearningTaskGenerator(Protocol):
    def generate(self, payload: dict[str, Any]) -> LearningTaskResult: ...


def required_task_focuses(payload: dict[str, Any]) -> tuple[str, ...]:
    """Return the one valid task sequence for the scene's relation count."""
    relationship_count = len(payload.get("relationships", []))
    return (
        REQUIRED_TASK_FOCUS_ORDER
        if relationship_count >= 1
        else REQUIRED_TASK_FOCUS_ORDER[:2] + REQUIRED_TASK_FOCUS_ORDER[3:]
    )


@lru_cache(maxsize=32)
def generation_response_model(
    focuses: tuple[str, ...],
    object_keys: tuple[str, ...],
    attribute_keys: tuple[str, ...],
    relationship_keys: tuple[str, ...],
) -> type[ApiModel]:
    """Express runtime requirements in the provider schema before generation."""
    fields = {}
    for focus in focuses:
        base = (
            GeneratedSentenceBuilderQuestion if focus == "chainedDescription"
            else GeneratedDescriptionQuestion if focus == "sceneDescription"
            else GeneratedMultipleChoiceQuestion
        )
        references = {}
        for name, keys in (
            ("object_keys", object_keys),
            ("attribute_keys", attribute_keys),
            ("relationship_keys", relationship_keys),
        ):
            minimum = int(name == "object_keys" or (
                name == "relationship_keys" and bool(keys)
                and focus in {"sceneDescription", "chainedDescription"}
            ))
            references[name] = (
                list[Literal.__getitem__(keys)] if keys else list[str],
                Field(min_length=minimum) if keys else Field(max_length=0),
            )
        question = create_model(f"{focus}Question", __base__=base, **references)
        task = create_model(
            f"{focus}Task", __base__=GeneratedLearningTask,
            questions=(list[question], Field(min_length=2, max_length=4)),
        )
        fields[focus] = (task, ...)
    return create_model(
        f"RequiredLearningTasks{len(focuses)}",
        __base__=ApiModel,
        **fields,
    )


def scene_generation_response_model(payload: dict[str, Any]) -> type[ApiModel]:
    if not payload.get("objects"):
        raise LearningTaskGenerationError("Learning tasks need at least one scene object.")
    return generation_response_model(
        required_task_focuses(payload),
        *(tuple(dict.fromkeys(row["key"] for row in payload.get(field, [])))
          for field in KEY_FIELDS),
    )


def unpack_generated_tasks(payload: dict[str, Any], response: ApiModel) -> LearningTaskResult:
    # The enclosing field owns the focus and order, not model-written metadata.
    return LearningTaskResult(tasks=[
        GeneratedLearningTask.model_validate({
            **getattr(response, focus).model_dump(), "focus": focus,
        })
        for focus in required_task_focuses(payload)
    ])


GENERATION_FORMAT_INSTRUCTION = (
    "\nReturn an object with one required field for each requiredTaskFocuses entry, "
    "using that focus as the field name and its complete task as the value. "
    "Do not return a tasks array. Populate every required field with 2–4 questions."
)


def normalize_learning_task_references(
    payload: dict[str, Any], result: LearningTaskResult
) -> LearningTaskResult:
    """Repair unambiguous relation labels without guessing a spatial relationship."""
    rows = payload.get("relationships", [])
    relationship_keys = {row["key"] for row in rows}
    def label(value):
        return " ".join(value.casefold().replace("_", " ").split())

    for task in result.tasks:
        for question in task.questions:
            resolved = []
            for key in question.relationship_keys:
                if key in relationship_keys:
                    resolved.append(key)
                    continue
                matches = [row for row in rows if label(key) in {
                    label(row.get("source", "")), label(row.get("translation", ""))
                }]
                if len(matches) > 1:
                    objects = set(question.object_keys)
                    matches = [row for row in matches if
                        row.get("subjectObjectKey") in objects
                        and row.get("referenceObjectKey") in objects]
                if len(matches) == 1:
                    resolved.append(matches[0]["key"])
                else:
                    # Preserve invalid references so validation can report them.
                    resolved.append(key)
            question.relationship_keys = list(dict.fromkeys(resolved))
    return result


def validate_learning_tasks(payload: dict[str, Any], result: LearningTaskResult) -> None:
    expected_focuses = required_task_focuses(payload)
    actual_focuses = tuple(task.focus for task in result.tasks)
    if actual_focuses != expected_focuses:
        raise LearningTaskGenerationError(
            "Learning tasks must be "
            f"{', '.join(expected_focuses)}; received {', '.join(actual_focuses) or 'none'}."
        )
    supplied = {
        field: {row["key"] for row in payload.get(field, [])} for field in KEY_FIELDS
    }
    for task in result.tasks:
        if len({question.question_id for question in task.questions}) != len(task.questions):
            raise LearningTaskGenerationError("Question ids must be unique within a task.")
        for question in task.questions:
            option_ids = [option.option_id for option in question.options]
            if len(set(option_ids)) != len(option_ids):
                raise LearningTaskGenerationError("Option ids must be unique within a question.")
            if question.interaction_type == "multipleChoice":
                if len(question.options) != 4 or question.correct_option_id not in option_ids:
                    raise LearningTaskGenerationError(
                        "Every multiple-choice question needs four options and one correct answer."
                    )
            elif task.focus != "chainedDescription":
                raise LearningTaskGenerationError(
                    "Only chained-description tasks may use sentence building."
                )
            referenced = 0
            for field, attribute in KEY_FIELDS.items():
                keys = set(getattr(question, attribute))
                if not keys <= supplied[field]:
                    raise LearningTaskGenerationError(
                        f"Learning tasks referenced {field} outside the supplied scene."
                    )
                referenced += len(keys)
            if not referenced:
                raise LearningTaskGenerationError(
                    "Every question must reuse vocabulary supplied by the scene."
                )
            if task.focus in {"sceneDescription", "chainedDescription"} and not (
                question.translation or ""
            ).strip():
                raise LearningTaskGenerationError(
                    "Description questions need an English translation."
                )
            if task.focus == "sceneDescription" and len(
                keys_for(question, "relationship_keys")
            ) < 1:
                raise LearningTaskGenerationError(
                    f"Question {question.question_id} has no resolvable scene relationship."
                )
            if task.focus == "chainedDescription" and (
                question.interaction_type != "sentenceBuilding"
                or len(keys_for(question, "relationship_keys"))
                < min(1, len(supplied["relationships"]))
            ):
                raise LearningTaskGenerationError(
                    "Sentence building must use the relationships available in the scene."
                )


def keys_for(question, attribute: str) -> set[str]:
    return set(getattr(question, attribute))
