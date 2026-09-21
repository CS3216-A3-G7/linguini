"""OpenAI-backed translation of confirmed scene vocabulary."""

import json
import logging
from pathlib import Path
from typing import Any

from openai import OpenAI

from app.schemas.translation import SceneTranslationResult
from app.services.scene_translation import (
    DEFAULT_PROMPT_PATH,
    SceneTranslationError,
    validate_translation_terms,
)

logger = logging.getLogger(__name__)


class OpenAISceneTranslator:
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
            raise ValueError("OpenAI translation requires an API key and model.")
        self.model = model.strip()
        self.prompt = prompt_path.read_text(encoding="utf-8").strip()
        self.client = client or OpenAI(
            api_key=api_key.strip(), timeout=timeout_seconds, max_retries=2
        )

    def translate(self, payload: dict[str, Any]) -> SceneTranslationResult:
        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=self.prompt,
                input=json.dumps(payload, ensure_ascii=False),
                text_format=SceneTranslationResult,
            )
            result = response.output_parsed
            if result is None:
                raise SceneTranslationError("OpenAI returned no translation.")
            validate_translation_terms(payload, result)
            return result
        except SceneTranslationError:
            logger.exception("OpenAI returned an unusable scene translation")
            raise
        except Exception as exc:
            logger.exception("OpenAI scene translation failed (%s)", type(exc).__name__)
            raise SceneTranslationError("Scene translation failed.") from exc
