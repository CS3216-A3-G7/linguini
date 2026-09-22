"""OpenAI-backed, text-only Phase 1 I-Spy clue generation."""

import json
import logging
from pathlib import Path
from typing import Any

from openai import OpenAI

from app.schemas.ispy_clues import ISpyClueResult
from app.services.ispy_clues import (
    DEFAULT_PROMPT_PATH,
    ISpyClueGenerationError,
    scene_clue_response_model,
    validate_ispy_clues,
)

logger = logging.getLogger(__name__)


class OpenAIISpyClueGenerator:
    def __init__(
        self, api_key: str, model: str, *, client: Any | None = None,
        prompt_path: Path = DEFAULT_PROMPT_PATH, timeout_seconds: int = 60,
    ) -> None:
        if not api_key.strip() or not model.strip():
            raise ValueError("OpenAI I-Spy clues require an API key and model.")
        self.model = model.strip()
        self.prompt = prompt_path.read_text(encoding="utf-8").strip()
        self.client = client or OpenAI(
            api_key=api_key.strip(), timeout=timeout_seconds, max_retries=2
        )

    def generate(self, payload: dict[str, Any]) -> ISpyClueResult:
        response_model = scene_clue_response_model(payload)
        try:
            response = self.client.responses.parse(
                model=self.model, instructions=self.prompt,
                input=json.dumps(payload, ensure_ascii=False), text_format=response_model,
            )
            parsed = response.output_parsed
            if parsed is None:
                raise ISpyClueGenerationError("OpenAI returned no I-Spy clues.")
            result = ISpyClueResult.model_validate(parsed.model_dump())
            validate_ispy_clues(payload, result)
            return result
        except ISpyClueGenerationError:
            logger.exception("OpenAI returned unusable I-Spy clues")
            raise
        except Exception as exc:
            logger.exception("OpenAI I-Spy clue generation failed (%s)", type(exc).__name__)
            raise ISpyClueGenerationError("I-Spy clue generation failed.") from exc
