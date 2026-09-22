"""Provider-neutral I-Spy clue contract and scene-grounding validation."""

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import Field, create_model

from app.schemas.base import ApiModel
from app.schemas.ispy_clues import GeneratedISpyClue, ISpyClueResult
from app.services.scene_analysis import SceneAnalysisError

DEFAULT_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "i_spy_clues.txt"


class ISpyClueGenerationError(SceneAnalysisError):
    """The provider did not return safe, scene-grounded I-Spy clues."""


class ISpyClueGenerator(Protocol):
    def generate(self, payload: dict[str, Any]) -> ISpyClueResult: ...


@lru_cache(maxsize=32)
def _response_model(
    object_keys: tuple[str, ...], relationship_keys: tuple[str, ...]
) -> type[ApiModel]:
    clue = create_model(
        "GroundedISpyClue",
        __base__=GeneratedISpyClue,
        answer_object_key=(Literal.__getitem__(object_keys), ...),
        object_keys=(
            list[Literal.__getitem__(object_keys)], Field(min_length=1, max_length=1)
        ),
        relationship_keys=(
            list[Literal.__getitem__(relationship_keys)] if relationship_keys else list[str],
            Field() if relationship_keys else Field(max_length=0),
        ),
    )
    return create_model(
        "GroundedISpyClueResult",
        __base__=ISpyClueResult,
        clues=(list[clue], Field(min_length=1, max_length=2)),
    )


def scene_clue_response_model(payload: dict[str, Any]) -> type[ApiModel]:
    object_keys = tuple(dict.fromkeys(row["key"] for row in payload.get("objects", [])))
    if not object_keys:
        raise ISpyClueGenerationError("I-Spy clues need at least one scene object.")
    relationship_keys = tuple(
        dict.fromkeys(row["key"] for row in payload.get("relationships", []))
    )
    return _response_model(object_keys, relationship_keys)


def validate_ispy_clues(payload: dict[str, Any], result: ISpyClueResult) -> None:
    object_keys = {row["key"] for row in payload.get("objects", [])}
    relationship_keys = {row["key"] for row in payload.get("relationships", [])}
    answers = set()
    for clue in result.clues:
        if clue.answer_object_key not in object_keys:
            raise ISpyClueGenerationError("I-Spy clue answer is not in the supplied scene.")
        if clue.object_keys != [clue.answer_object_key]:
            raise ISpyClueGenerationError("Each I-Spy clue must reference its answer object only.")
        if not set(clue.relationship_keys) <= relationship_keys:
            raise ISpyClueGenerationError("I-Spy clue used a relationship outside the scene.")
        if clue.answer_object_key in answers:
            raise ISpyClueGenerationError("I-Spy clues must have different answers.")
        answers.add(clue.answer_object_key)
        if clue.clue.casefold().lstrip().startswith(("i spy", "je vois", "veo ")):
            raise ISpyClueGenerationError("I-Spy clue must contain only the phrase ending.")
