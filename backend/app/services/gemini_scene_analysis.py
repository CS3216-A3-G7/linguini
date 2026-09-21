"""Gemini-backed scene extraction for user-supplied images."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any
from uuid import uuid5

from google import genai
from google.genai import types

from app.schemas.media import MediaAsset, SceneObject, SceneObjectRelation
from app.schemas.scene_analysis import SceneAnalysisModelResult
from app.schemas.sessions import Session
from app.services.image_storage import ImageStorage
from app.services.scene_analysis import SceneAnalysisError, SceneAnalysisResult
from app.services.scene_analysis_validation import parse_scene_analysis

MIN_OBJECT_CONFIDENCE = 0.7
MIN_RELATION_CONFIDENCE = 0.7
DEFAULT_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "scene_analysis.txt"


class GeminiSceneAnalyzer:
    def __init__(
        self,
        storage: ImageStorage,
        api_key: str,
        model: str,
        *,
        client: Any | None = None,
        prompt_path: Path = DEFAULT_PROMPT_PATH,
    ) -> None:
        if not api_key.strip() or not model.strip():
            raise ValueError("Gemini scene analysis requires an API key and model.")
        self.storage = storage
        self.model = model.strip()
        self.prompt = prompt_path.read_text(encoding="utf-8").strip()
        self.client = client or genai.Client(
            api_key=api_key.strip(),
            http_options=types.HttpOptions(timeout=30_000),
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
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    "Extract useful vocabulary objects from this image.",
                    types.Part.from_bytes(data=image, mime_type=asset.mime_type),
                ],
                config=types.GenerateContentConfig(
                    system_instruction=self.prompt,
                    temperature=0,
                    response_mime_type="application/json",
                    response_json_schema=SceneAnalysisModelResult.model_json_schema(
                        by_alias=True
                    ),
                ),
            )
            if not response.text:
                raise SceneAnalysisError("Gemini returned no scene analysis.")
            result = parse_scene_analysis(response.text)
            return self._to_domain(session, result)
        except SceneAnalysisError:
            raise
        except Exception as exc:
            raise SceneAnalysisError("Gemini scene analysis failed.") from exc

    @staticmethod
    def _to_domain(
        session: Session, result: SceneAnalysisModelResult
    ) -> SceneAnalysisResult:
        retained = [
            item for item in result.objects if item.confidence >= MIN_OBJECT_CONFIDENCE
        ]
        if not retained:
            raise SceneAnalysisError("No reliable learning objects were found.")

        object_ids = {
            item.key: uuid5(session.id, f"gemini-scene-object:{item.key}")
            for item in retained
        }
        objects = [
            SceneObject(
                id=object_ids[item.key],
                session_id=session.id,
                label=item.label,
                bounding_box=item.bounding_box.model_dump(),
                attributes=item.attributes,
                confidence_score=item.confidence,
                source_object_key=item.key,
            )
            for item in retained
        ]
        relations = [
            SceneObjectRelation(
                id=uuid5(session.id, f"gemini-scene-relation:{item.key}"),
                subject_scene_object_id=object_ids[item.source_object_key],
                relation=item.relation_type.value,
                reference_scene_object_id=object_ids[item.target_object_key],
                source_relation_key=item.key,
            )
            for item in result.relations
            if item.confidence >= MIN_RELATION_CONFIDENCE
            and item.source_object_key in object_ids
            and item.target_object_key in object_ids
        ]
        return SceneAnalysisResult(
            title=result.title,
            summary=result.summary,
            objects=objects,
            relations=relations,
        )


class RoutedSceneAnalyzer:
    """Keep curated scenes deterministic; send only user images to Gemini."""

    def __init__(self, curated: Any, uploaded: GeminiSceneAnalyzer) -> None:
        self.curated = curated
        self.uploaded = uploaded

    def analyze(self, session, asset, profile, scene) -> SceneAnalysisResult:
        analyzer = self.curated if asset.source == "preloaded" else self.uploaded
        return analyzer.analyze(session, asset, profile, scene)
