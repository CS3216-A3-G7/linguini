"""Gemini-backed translation of confirmed scene vocabulary."""

import json
import logging
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from app.schemas.translation import SceneTranslationResult
from app.services.scene_translation import (
    DEFAULT_PROMPT_PATH,
    SceneTranslationError,
    validate_translation_terms,
)

logger = logging.getLogger(__name__)


class GeminiSceneTranslator:
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        client: Any | None = None,
        prompt_path: Path = DEFAULT_PROMPT_PATH,
        timeout_seconds: int = 60,
    ) -> None:
        if not api_key.strip() or not model.strip():
            raise ValueError("Gemini translation requires an API key and model.")
        self.model = model.strip()
        self.prompt = prompt_path.read_text(encoding="utf-8").strip()
        self.client = client or genai.Client(
            api_key=api_key.strip(),
            http_options=types.HttpOptions(timeout=timeout_seconds * 1_000),
        )

    def translate(self, payload: dict[str, Any]) -> SceneTranslationResult:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=json.dumps(payload, ensure_ascii=False),
                config=types.GenerateContentConfig(
                    system_instruction=self.prompt,
                    temperature=0,
                    response_mime_type="application/json",
                    response_json_schema=SceneTranslationResult.model_json_schema(
                        by_alias=True
                    ),
                ),
            )
            if not response.text:
                raise SceneTranslationError("Gemini returned no translation.")
            result = SceneTranslationResult.model_validate_json(response.text)
            validate_translation_terms(payload, result)
            return result
        except SceneTranslationError:
            logger.exception("Gemini returned an unusable scene translation")
            raise
        except Exception as exc:
            logger.exception("Gemini scene translation failed (%s)", type(exc).__name__)
            raise SceneTranslationError("Scene translation failed.") from exc
