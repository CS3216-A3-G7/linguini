from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.schemas.media import MediaAsset
from app.schemas.sessions import Session
from app.services.openai_scene_analysis import (
    OpenAISceneAnalysisResult,
    OpenAISceneAnalyzer,
)


def test_openai_scene_analysis_sends_image_and_uses_shared_contract(tmp_path: Path):
    prompt = tmp_path / "scene.txt"
    prompt.write_text("Only report visible objects.", encoding="utf-8")
    parsed = OpenAISceneAnalysisResult.model_validate(
        {
            "title": "Desk",
            "summary": "A cup is on a table.",
            "objects": [
                {
                    "key": "object_1",
                    "label": "cup",
                    "confidence": 0.95,
                    "boundingBox": {"x": 0.1, "y": 0.1, "width": 0.2, "height": 0.2},
                    "attributes": [{"type": "color", "value": "red"}],
                },
                {
                    "key": "object_2",
                    "label": "table",
                    "confidence": 0.9,
                    "boundingBox": {"x": 0.05, "y": 0.4, "width": 0.8, "height": 0.5},
                    "attributes": [],
                },
            ],
            "relations": [
                {
                    "key": "relation_1",
                    "relationType": "on",
                    "sourceObjectKey": "object_1",
                    "targetObjectKey": "object_2",
                    "confidence": 0.9,
                }
            ],
        }
    )
    client = SimpleNamespace(
        responses=SimpleNamespace(
            parse=MagicMock(return_value=SimpleNamespace(output_parsed=parsed))
        )
    )
    storage = MagicMock()
    storage.download.return_value = b"image-bytes"
    provider = OpenAISceneAnalyzer(
        storage,
        "test-key",
        "test-model",
        client=client,
        prompt_path=prompt,
    )
    session = Session(
        user_id="11111111-1111-4111-8111-111111111111",
        language_profile_id="22222222-2222-4222-8222-222222222222",
        scene_media_asset_id="33333333-3333-4333-8333-333333333333",
    )
    asset = MediaAsset(
        id=session.scene_media_asset_id,
        owner_user_id=session.user_id,
        media_type="image",
        source="userUpload",
        storage_key="users/test/photo.jpg",
        mime_type="image/jpeg",
        width=100,
        height=100,
    )

    result = provider.analyze(session, asset, {}, None)

    assert [item.label for item in result.objects] == ["cup", "table"]
    assert result.objects[0].attributes == {"color": "red"}
    assert result.relations[0].relation == "on"
    call = client.responses.parse.call_args.kwargs
    assert call["text_format"] is OpenAISceneAnalysisResult
    image_part = call["input"][0]["content"][1]
    assert image_part["image_url"].startswith("data:image/jpeg;base64,")
    storage.download.assert_called_once_with(asset.storage_key)
