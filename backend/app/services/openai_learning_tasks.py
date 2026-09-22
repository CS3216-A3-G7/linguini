"""OpenAI-backed generation of grammar learning tasks."""

import json
import logging
from pathlib import Path
from typing import Any

from openai import OpenAI

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


class OpenAILearningTaskGenerator:
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
            raise ValueError("OpenAI learning tasks require an API key and model.")
        self.model = model.strip()
        self.prompt = prompt_path.read_text(encoding="utf-8").strip()
        self.client = client or OpenAI(
            api_key=api_key.strip(), timeout=timeout_seconds, max_retries=2
        )

    def generate(self, payload: dict[str, Any]) -> LearningTaskResult:
        focuses = required_task_focuses(payload)
        payload = {**payload, "requiredTaskFocuses": list(focuses)}
        response_model = generation_response_model(focuses)
        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=self.prompt + GENERATION_FORMAT_INSTRUCTION,
                input=json.dumps(payload, ensure_ascii=False),
                text_format=response_model,
            )
            result = response.output_parsed
            if result is None:
                raise LearningTaskGenerationError("OpenAI returned no learning tasks.")
            result = unpack_generated_tasks(payload, result)
            result = normalize_learning_task_references(payload, result)
            validate_learning_tasks(payload, result)
            return result
        except LearningTaskGenerationError:
            logger.exception("OpenAI returned unusable learning tasks")
            raise
        except Exception as exc:
            logger.exception("OpenAI learning task generation failed (%s)", type(exc).__name__)
            raise LearningTaskGenerationError("Learning task generation failed.") from exc
