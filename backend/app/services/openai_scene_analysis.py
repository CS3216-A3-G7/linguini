"""OpenAI-backed scene extraction for user-supplied images."""

import base64
import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from openai import OpenAI

from app.schemas.base import ApiModel
from app.schemas.enums import SceneRelationType
from app.schemas.media import MediaAsset
from app.schemas.scene_analysis import ModelBoundingBox, SceneAnalysisModelResult
from app.schemas.sessions import Session
from app.services.gemini_scene_analysis import (
    DEFAULT_PROMPT_PATH,
    model_result_to_domain,
)
from app.services.image_storage import ImageStorage
from app.services.scene_analysis import SceneAnalysisError, SceneAnalysisResult
from app.services.scene_analysis_validation import parse_scene_analysis

logger = logging.getLogger(__name__)


class OpenAIAttribute(ApiModel):
    type: str
    value: str


class OpenAISceneObject(ApiModel):
    key: str
    label: str
    confidence: float
    bounding_box: ModelBoundingBox
    anchor_point: dict[str, float] | None = None
    attributes: list[OpenAIAttribute]


class OpenAISceneRelation(ApiModel):
    key: str
    relation_type: SceneRelationType
    source_object_key: str
    target_object_key: str
    confidence: float


class OpenAISceneAnalysisResult(ApiModel):
    title: str
    summary: str
    objects: list[OpenAISceneObject]
    relations: list[OpenAISceneRelation]


class OpenAISceneAnalyzer:
    def __init__(
        self,
        storage: ImageStorage,
        api_key: str,
        model: str,
        *,
        client: Any | None = None,
        prompt_path: Path = DEFAULT_PROMPT_PATH,
        timeout_seconds: int = 120,
    ) -> None:
        if not api_key.strip() or not model.strip():
            raise ValueError("OpenAI scene analysis requires an API key and model.")
        self.storage = storage
        self.model = model.strip()
        self.prompt = prompt_path.read_text(encoding="utf-8").strip()
        self.client = client or OpenAI(
            api_key=api_key.strip(), timeout=timeout_seconds, max_retries=2
        )

    def analyze(
        self,
        session: Session,
        asset: MediaAsset,
        profile: Mapping[str, Any],
        scene: Mapping[str, Any] | None,
    ) -> SceneAnalysisResult:
        del profile, scene
        try:
            image = self.storage.download(asset.storage_key)
            encoded = base64.b64encode(image).decode("ascii")
            response = self.client.responses.parse(
                model=self.model,
                instructions=self.prompt,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "Extract useful vocabulary objects from this image.",
                            },
                            {
                                "type": "input_image",
                                "image_url": f"data:{asset.mime_type};base64,{encoded}",
                                "detail": "high",
                            },
                        ],
                    }
                ],
                text_format=OpenAISceneAnalysisResult,
            )
            result = response.output_parsed
            if result is None:
                raise SceneAnalysisError("OpenAI returned no scene analysis.")
            common_result = parse_scene_analysis(
                SceneAnalysisModelResult(
                    title=result.title,
                    summary=result.summary,
                    objects=[
                        {
                            "key": item.key,
                            "label": item.label,
                            "confidence": item.confidence,
                            "boundingBox": item.bounding_box.model_dump(),
                            "anchorPoint": item.anchor_point,
                            "attributes": {
                                attribute.type: attribute.value
                                for attribute in item.attributes
                            },
                        }
                        for item in result.objects
                    ],
                    relations=[row.model_dump() for row in result.relations],
                ).model_dump_json(by_alias=True)
            )
            return model_result_to_domain(session, common_result)
        except SceneAnalysisError:
            logger.exception(
                "OpenAI returned an unusable scene analysis for session %s", session.id
            )
            raise
        except Exception as exc:
            logger.exception(
                "OpenAI scene analysis failed for session %s (%s)",
                session.id,
                type(exc).__name__,
            )
            raise SceneAnalysisError("OpenAI scene analysis failed.") from exc
