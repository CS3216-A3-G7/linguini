"""Provider-neutral orchestrator for model-backed scene translation.

Builds the shared versioned request, calls a ``TextModelClient``, validates
the returned text locally, and returns the domain result. Contains no
provider-specific logic. Learner-supplied content reaches the tracer only
through ``record_content``, which is gated by the capture-content setting.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from pydantic import ValidationError

from app.ai.features.translation.prompt import (
    SCENE_TRANSLATION_PROMPT_VERSION,
    SCENE_TRANSLATION_SCHEMA_VERSION,
    SCENE_TRANSLATION_SYSTEM_PROMPT,
)
from app.ai.features.translation.schemas import (
    SceneTranslationRequest,
    SceneTranslationResult,
)
from app.ai.features.translation.validation import (
    SceneTranslationError,
    validate_translation_terms,
)
from app.ai.model_errors import ProviderError
from app.ai.observability import AITracer
from app.ai.settings import AiFeature
from app.ai.text_model import TextModelClient, TextModelConfig, TextModelRequest
from app.services.vision_model import build_strict_json_schema

logger = logging.getLogger(__name__)

_TRANSLATION_INVALID = "translationInvalid"


def build_scene_translation_schema() -> dict[str, Any]:
    """Strict JSON schema for the shared translation output contract."""
    return build_strict_json_schema(SceneTranslationResult)


class SceneTranslationService:
    """Translates confirmed scene vocabulary through the text-model seam."""

    def __init__(
        self,
        client: TextModelClient,
        config: TextModelConfig,
        *,
        tracer: AITracer,
        provider: str,
    ) -> None:
        self._client = client
        self._config = config
        self._tracer = tracer
        self._provider = provider
        self._json_schema = build_scene_translation_schema()

    def translate(self, payload: dict[str, Any]) -> SceneTranslationResult:
        try:
            parsed_payload = SceneTranslationRequest.model_validate(payload)
        except ValidationError as error:
            raise SceneTranslationError(
                "Translation request payload is invalid."
            ) from error

        content = json.dumps(payload, ensure_ascii=False)
        request = TextModelRequest(
            system_prompt=SCENE_TRANSLATION_SYSTEM_PROMPT,
            user_content=content,
            json_schema_name="scene_translation_v1",
            json_schema=self._json_schema,
            prompt_version=SCENE_TRANSLATION_PROMPT_VERSION,
        )

        attempts = 1 + self._config.max_retries
        latency_ms = 0.0
        with self._tracer.generation(
            "scene-translation",
            feature=AiFeature.SCENE_TRANSLATION.value,
            provider=self._provider,
            model=self._config.model_name,
            prompt_version=SCENE_TRANSLATION_PROMPT_VERSION,
            schema_version=SCENE_TRANSLATION_SCHEMA_VERSION,
            model_parameters={
                "maxOutputTokens": self._config.max_output_tokens,
                "timeoutSeconds": self._config.timeout_seconds,
            },
        ) as generation:
            for attempt in range(1, attempts + 1):
                call_start = time.perf_counter()
                try:
                    response = self._client.generate(request)
                except ProviderError as error:
                    latency_ms += (time.perf_counter() - call_start) * 1000
                    if error.transient and attempt < attempts:
                        logger.warning(
                            "scene translation attempt failed, retrying",
                            extra={
                                "attempt": attempt,
                                "code": error.code.value,
                            },
                        )
                        continue
                    generation.update(
                        latency_ms=latency_ms,
                        retry_count=attempt - 1,
                        validation_result="invalid",
                        error_code=error.code.value,
                    )
                    raise SceneTranslationError(
                        "Scene translation failed."
                    ) from error
                latency_ms += (time.perf_counter() - call_start) * 1000

                try:
                    result = SceneTranslationResult.model_validate_json(
                        response.output_text
                    )
                    validate_translation_terms(parsed_payload, result)
                except (ValueError, SceneTranslationError) as error:
                    if attempt < attempts:
                        logger.warning(
                            "scene translation output failed validation, retrying",
                            extra={"attempt": attempt},
                        )
                        continue
                    generation.update(
                        latency_ms=latency_ms,
                        retry_count=attempt - 1,
                        validation_result="invalid",
                        error_code=_TRANSLATION_INVALID,
                    )
                    raise SceneTranslationError(
                        "Scene translation returned unusable output."
                    ) from error

                generation.update(
                    latency_ms=latency_ms,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    retry_count=attempt - 1,
                    validation_result="valid",
                )
                generation.record_content(
                    input=content, output=response.output_text
                )
                return result

            # Unreachable: every loop path either returns or raises.
            raise SceneTranslationError("Scene translation failed.")
