"""Gemini-backed generation of grammar learning tasks."""

import json
import logging
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from app.schemas.learning_tasks import LearningTaskResult
from app.services.learning_tasks import (
    DEFAULT_PROMPT_PATH,
    GENERATION_FORMAT_INSTRUCTION,
    LearningTaskGenerationError,
    generation_response_model,
    normalize_learning_task_references,
    required_task_focuses,
    unpack_generated_tasks,
    validate_learning_tasks,
)

logger = logging.getLogger(__name__)


class GeminiLearningTaskGenerator:
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
            raise ValueError("Gemini learning tasks require an API key and model.")
        self.model = model.strip()
        self.prompt = prompt_path.read_text(encoding="utf-8").strip()
        self.client = client or genai.Client(
            api_key=api_key.strip(),
            http_options=types.HttpOptions(timeout=timeout_seconds * 1_000),
        )

    def generate(self, payload: dict[str, Any]) -> LearningTaskResult:
        focuses = required_task_focuses(payload)
        payload = {**payload, "requiredTaskFocuses": list(focuses)}
        response_model = generation_response_model(focuses)
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=json.dumps(payload, ensure_ascii=False),
                config=types.GenerateContentConfig(
                    system_instruction=self.prompt + GENERATION_FORMAT_INSTRUCTION,
                    temperature=0,
                    response_mime_type="application/json",
                    response_json_schema=response_model.model_json_schema(by_alias=True),
                ),
            )
            if not response.text:
                raise LearningTaskGenerationError("Gemini returned no learning tasks.")
            result = unpack_generated_tasks(
                payload, response_model.model_validate_json(response.text)
            )
            result = normalize_learning_task_references(payload, result)
            validate_learning_tasks(payload, result)
            return result
        except LearningTaskGenerationError:
            logger.exception("Gemini returned unusable learning tasks")
            raise
        except Exception as exc:
            logger.exception("Gemini learning task generation failed (%s)", type(exc).__name__)
            raise LearningTaskGenerationError("Learning task generation failed.") from exc
