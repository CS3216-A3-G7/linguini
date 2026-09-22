"""Provider-neutral grammar learning-task contract and validation."""

from pathlib import Path
from typing import Any, Protocol

from app.schemas.learning_tasks import REQUIRED_TASK_FOCUS_ORDER, LearningTaskResult
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


def normalize_learning_task_references(
    payload: dict[str, Any], result: LearningTaskResult
) -> LearningTaskResult:
    """Discard non-semantic relationship metadata a model may echo incorrectly.

    Relationship keys are opaque database IDs, unlike the translated relationship
    words shown in a lesson. Keeping an unknown key would not change lesson text,
    so remove it before validation while retaining strict object and attribute
    provenance checks.
    """
    relationship_keys = {row["key"] for row in payload.get("relationships", [])}
    for task in result.tasks:
        for question in task.questions:
            question.relationship_keys = [
                key for key in question.relationship_keys if key in relationship_keys
            ]
    return result


def validate_learning_tasks(payload: dict[str, Any], result: LearningTaskResult) -> None:
    relationship_count = len(payload.get("relationships", []))
    expected_focuses = (
        REQUIRED_TASK_FOCUS_ORDER
        if relationship_count >= 2
        else REQUIRED_TASK_FOCUS_ORDER[:3]
        if relationship_count == 1
        else REQUIRED_TASK_FOCUS_ORDER[:1]
    )
    if tuple(task.focus for task in result.tasks) != expected_focuses:
        raise LearningTaskGenerationError(
            "Learning tasks do not match the relationships available in this scene."
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
            if question.correct_option_id not in option_ids:
                raise LearningTaskGenerationError(
                    "Every question needs exactly one correct option it offers."
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
            if task.focus in {"prepositionRelation", "sceneDescription"} and not keys_for(
                question, "relationship_keys"
            ):
                raise LearningTaskGenerationError(
                    "Relation tasks must reference a supplied relationship."
                )
            if task.focus == "chainedDescription" and len(
                keys_for(question, "relationship_keys")
            ) < 2:
                raise LearningTaskGenerationError(
                    "Chained-description questions must reference two relationships."
                )


def keys_for(question, attribute: str) -> set[str]:
    return set(getattr(question, attribute))
