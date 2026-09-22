"""Provider-neutral scene translation contract and validation."""

from pathlib import Path
from typing import Any, Protocol

from app.schemas.translation import SceneTranslationResult
from app.services.scene_analysis import SceneAnalysisError

DEFAULT_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "scene_translation.txt"


class SceneTranslationError(SceneAnalysisError):
    """The confirmed scene could not be translated reliably."""


class SceneTranslator(Protocol):
    def translate(self, payload: dict[str, Any]) -> SceneTranslationResult: ...


def validate_translation_terms(
    payload: dict[str, Any], result: SceneTranslationResult
) -> None:
    for field in ("objects", "attributes", "relationships"):
        supplied = {(row["key"], row["source"]) for row in payload[field]}
        returned = {(row.key, row.source) for row in getattr(result, field)}
        if supplied != returned:
            raise SceneTranslationError(
                f"Translation changed or omitted supplied {field}."
            )
    if any(not row.article for row in result.objects):
        raise SceneTranslationError("Every translated object requires a definite article.")
    if any(row.article or row.gender for row in [*result.attributes, *result.relationships]):
        raise SceneTranslationError("Only object translations may include articles or gender.")
