"""Provider-neutral, deterministic validation for scene translations.

No SDK imports: the same rules run regardless of which adapter produced the
response. ``SceneTranslationError`` stays a ``SceneAnalysisError`` so the
workflow and learning-error handling are unchanged.
"""

from __future__ import annotations

from typing import Any

from app.ai.features.translation.schemas import (
    SceneTranslationRequest,
    SceneTranslationResult,
)
from app.services.scene_analysis import SceneAnalysisError


class SceneTranslationError(SceneAnalysisError):
    """The confirmed scene could not be translated reliably."""


def _supplied_terms(payload: dict[str, Any] | SceneTranslationRequest, field: str) -> set:
    rows = getattr(payload, field) if isinstance(
        payload, SceneTranslationRequest
    ) else payload[field]
    return {(row.key if hasattr(row, "key") else row["key"],
             row.source if hasattr(row, "source") else row["source"])
            for row in rows}


def validate_translation_terms(
    payload: dict[str, Any] | SceneTranslationRequest,
    result: SceneTranslationResult,
) -> None:
    for field in ("objects", "attributes", "relationships"):
        supplied = _supplied_terms(payload, field)
        returned = {(row.key, row.source) for row in getattr(result, field)}
        if supplied != returned:
            raise SceneTranslationError(
                f"Translation changed or omitted supplied {field}."
            )
    if any(not row.article for row in result.objects):
        raise SceneTranslationError(
            "Every translated object requires a definite article."
        )
    if any(
        row.article or row.gender
        for row in [*result.attributes, *result.relationships]
    ):
        raise SceneTranslationError(
            "Only object translations may include articles or gender."
        )
