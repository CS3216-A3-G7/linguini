"""Orchestrating service for model-backed scene analysis.

Builds the versioned scene-analysis request, calls a ``VisionModelClient``,
and validates the returned text locally with ``parse_scene_analysis``. Performs
no database writes.
"""

from __future__ import annotations

import logging
from enum import StrEnum

from app.schemas.scene_analysis import SceneAnalysisModelResult
from app.services.prompts.scene_analysis_v1 import (
    SCENE_ANALYSIS_PROMPT_VERSION,
    SCENE_ANALYSIS_SYSTEM_PROMPT,
    SCENE_ANALYSIS_USER_INSTRUCTION,
)
from app.services.scene_analysis import SceneAnalysisError
from app.services.scene_analysis_validation import (
    SceneAnalysisValidationError,
    parse_scene_analysis,
)
from app.services.vision_model import (
    VisionImage,
    VisionModelClient,
    VisionModelConfig,
    VisionModelError,
    VisionModelErrorCode,
    VisionModelRequest,
    build_strict_json_schema,
)

logger = logging.getLogger(__name__)


class SceneAnalysisModelErrorCode(StrEnum):
    """Stable application error codes for model-backed scene analysis."""

    MODEL_OUTPUT_INVALID = "modelOutputInvalid"


class SceneAnalysisModelError(SceneAnalysisError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class ModelSceneAnalyzer:
    def __init__(self, client: VisionModelClient, config: VisionModelConfig) -> None:
        self._client = client
        self._config = config
        self._json_schema = build_strict_json_schema(SceneAnalysisModelResult)

    def analyze(self, image: VisionImage) -> SceneAnalysisModelResult:
        request = VisionModelRequest(
            image=image,
            system_prompt=SCENE_ANALYSIS_SYSTEM_PROMPT,
            user_instruction=SCENE_ANALYSIS_USER_INSTRUCTION,
            json_schema_name="scene_analysis_v1",
            json_schema=self._json_schema,
            prompt_version=SCENE_ANALYSIS_PROMPT_VERSION,
        )

        attempts = 1 + self._config.max_retries
        for attempt in range(1, attempts + 1):
            try:
                response = self._client.generate(request)
                return parse_scene_analysis(response.output_text)
            except VisionModelError as error:
                retryable = error.transient or (
                    error.code is VisionModelErrorCode.PROVIDER_RESPONSE_INVALID
                )
                if retryable and attempt < attempts:
                    logger.warning(
                        "scene analysis attempt failed, retrying",
                        extra={"attempt": attempt, "code": error.code.value},
                    )
                    continue
                if error.code is VisionModelErrorCode.PROVIDER_RESPONSE_INVALID:
                    raise SceneAnalysisModelError(
                        SceneAnalysisModelErrorCode.MODEL_OUTPUT_INVALID,
                        "scene analysis model returned invalid output",
                    ) from error
                raise SceneAnalysisModelError(error.code.value, str(error)) from error
            except SceneAnalysisValidationError as error:
                if attempt < attempts:
                    logger.warning(
                        "scene analysis output failed validation, retrying",
                        extra={"attempt": attempt},
                    )
                    continue
                raise SceneAnalysisModelError(
                    SceneAnalysisModelErrorCode.MODEL_OUTPUT_INVALID,
                    "scene analysis model returned output that failed validation",
                ) from error

        raise SceneAnalysisModelError(
            SceneAnalysisModelErrorCode.MODEL_OUTPUT_INVALID,
            "scene analysis model returned invalid output",
        )
