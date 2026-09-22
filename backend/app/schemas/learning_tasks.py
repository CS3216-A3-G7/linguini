"""Structured contracts for generated grammar learning tasks."""

from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from app.schemas.base import ApiModel, NonEmptyText

type LearningTaskFocus = Literal[
    "genderNumberAgreement",
    "pluralNounForm",
    "sceneDescription",
    "chainedDescription",
]

REQUIRED_TASK_FOCUS_ORDER: tuple[str, ...] = (
    "genderNumberAgreement",
    "pluralNounForm",
    "sceneDescription",
    "chainedDescription",
)


class GeneratedChoice(ApiModel):
    option_id: NonEmptyText
    label: NonEmptyText


class GeneratedQuestion(ApiModel):
    question_id: NonEmptyText
    prompt: NonEmptyText
    interaction_type: Literal["multipleChoice", "sentenceBuilding"] = "multipleChoice"
    options: list[GeneratedChoice] = Field(default_factory=list)
    correct_option_id: NonEmptyText | None = None
    correct_text: str | None = None
    token_bank: list[NonEmptyText] = Field(default_factory=list)
    translation: str | None = None
    object_keys: list[str] = Field(default_factory=list)
    attribute_keys: list[str] = Field(default_factory=list)
    relationship_keys: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def discard_builder_fields_from_multiple_choice(cls, value: Any) -> Any:
        """Tolerate harmless answer text a model may echo beside a valid MCQ.

        Only chained descriptions are sentence builders. A correct option remains
        the server-side answer key for every other task, so retaining an echoed
        `correctText` or `tokenBank` adds no value and makes the response invalid.
        """
        if not isinstance(value, dict):
            return value
        interaction = value.get(
            "interactionType", value.get("interaction_type", "multipleChoice")
        )
        if interaction != "multipleChoice":
            return value
        normalized = {
            key: item
            for key, item in value.items()
            if key not in {"correctText", "correct_text", "tokenBank", "token_bank"}
        }
        # Explicit values keep these optional fields available during assignment
        # validation, even when the provider omitted them from its JSON.
        normalized["correct_text"] = None
        normalized["token_bank"] = []
        return normalized

    @model_validator(mode="after")
    def validate_interaction(self) -> "GeneratedQuestion":
        if self.interaction_type == "multipleChoice":
            if len(self.options) != 4:
                raise ValueError("multiple-choice questions require exactly four options")
            option_ids = {option.option_id for option in self.options}
            if self.correct_option_id not in option_ids:
                raise ValueError("correctOptionId must identify an offered option")
            if getattr(self, "correct_text", None) is not None or getattr(self, "token_bank", []):
                raise ValueError("multiple-choice questions cannot include sentence-building data")
        elif not self.correct_text or not self.token_bank:
            raise ValueError("sentence-building questions require correctText and tokenBank")
        elif self.options or self.correct_option_id is not None:
            raise ValueError("sentence-building questions cannot include answer options")
        return self


class GeneratedMultipleChoiceQuestion(GeneratedQuestion):
    interaction_type: Literal["multipleChoice"] = "multipleChoice"
    options: list[GeneratedChoice] = Field(min_length=4, max_length=4)
    correct_option_id: NonEmptyText


class GeneratedDescriptionQuestion(GeneratedMultipleChoiceQuestion):
    translation: NonEmptyText = Field(
        description="English translation of the complete correct sentence. Never null or empty."
    )


class GeneratedSentenceBuilderQuestion(GeneratedQuestion):
    interaction_type: Literal["sentenceBuilding"] = "sentenceBuilding"
    options: list[GeneratedChoice] = Field(default_factory=list, max_length=0)
    correct_option_id: None = None
    correct_text: NonEmptyText
    token_bank: list[NonEmptyText] = Field(min_length=1)
    translation: NonEmptyText = Field(
        description="Complete English sentence the learner must translate using the word bank."
    )


class GeneratedLearningTask(ApiModel):
    focus: LearningTaskFocus
    title: NonEmptyText
    explanation: NonEmptyText
    questions: Annotated[list[GeneratedQuestion], Field(min_length=2, max_length=4)]


class LearningTaskResult(ApiModel):
    tasks: Annotated[
        list[GeneratedLearningTask],
        Field(min_length=1, max_length=len(REQUIRED_TASK_FOCUS_ORDER)),
    ]
