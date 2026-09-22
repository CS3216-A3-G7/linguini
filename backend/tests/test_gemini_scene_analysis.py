from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.schemas.media import MediaAsset
from app.schemas.sessions import Session
from app.services.gemini_scene_analysis import GeminiSceneAnalyzer, RoutedSceneAnalyzer
from app.services.scene_analysis import SceneAnalysisError


def analyzer(tmp_path: Path, payload: str):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Only report visible objects.", encoding="utf-8")
    client = SimpleNamespace(
        models=SimpleNamespace(generate_content=MagicMock(return_value=SimpleNamespace(text=payload)))
    )
    storage = MagicMock()
    storage.download.return_value = b"image-bytes"
    return GeminiSceneAnalyzer(
        storage,
        "test-key",
        "test-model",
        client=client,
        prompt_path=prompt,
    ), client, storage


def session_and_asset():
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
    return session, asset


def test_gemini_analyzer_sends_image_and_converts_validated_result(tmp_path):
    payload = """{
      "title":"Desk", "summary":"A cup is on a table.",
      "objects":[
        {"key":"object_1","label":"cup","confidence":0.95,
         "boundingBox":{"x":0.1,"y":0.1,"width":0.2,"height":0.2},
         "attributes":{"color":"red"}},
        {"key":"object_2","label":"table","confidence":0.9,
         "boundingBox":{"x":0.05,"y":0.4,"width":0.8,"height":0.5},
         "attributes":{"material":"wood"}}
      ],
      "relations":[{"key":"relation_1","relationType":"on",
        "sourceObjectKey":"object_1","targetObjectKey":"object_2","confidence":0.9}]
    }"""
    provider, client, storage = analyzer(tmp_path, payload)
    session, asset = session_and_asset()

    result = provider.analyze(session, asset, {}, None)

    assert [item.label for item in result.objects] == ["cup", "table"]
    assert result.objects[0].attributes == {"color": "red"}
    assert result.relations[0].relation == "on"
    storage.download.assert_called_once_with(asset.storage_key)
    request = client.models.generate_content.call_args.kwargs
    assert request["model"] == "test-model"
    assert request["config"].response_mime_type == "application/json"


def test_low_confidence_objects_and_their_relations_are_removed(tmp_path):
    payload = """{
      "title":"Desk", "summary":"A cup may be near a table.",
      "objects":[
        {"key":"cup","label":"cup","confidence":0.69,
         "boundingBox":{"x":0.1,"y":0.1,"width":0.2,"height":0.2},"attributes":{}},
        {"key":"table","label":"table","confidence":0.9,
         "boundingBox":{"x":0.1,"y":0.4,"width":0.8,"height":0.5},"attributes":{}}
      ],
      "relations":[{"key":"near","relationType":"near","sourceObjectKey":"cup",
        "targetObjectKey":"table","confidence":0.9}]
    }"""
    provider, _, _ = analyzer(tmp_path, payload)
    session, asset = session_and_asset()

    result = provider.analyze(session, asset, {}, None)

    assert [item.label for item in result.objects] == ["table"]
    assert result.relations == []


def test_no_reliable_objects_fails_without_inventing_content(tmp_path):
    payload = '{"title":"Unclear Scene","summary":"Nothing is clear.","objects":[],"relations":[]}'
    provider, _, _ = analyzer(tmp_path, payload)
    session, asset = session_and_asset()

    with pytest.raises(SceneAnalysisError, match="No reliable"):
        provider.analyze(session, asset, {}, None)


def test_preloaded_scene_uses_curated_analyzer():
    curated = MagicMock()
    uploaded = MagicMock()
    session, _ = session_and_asset()
    asset = MediaAsset(
        id=session.scene_media_asset_id,
        media_type="image",
        source="preloaded",
        storage_key="preloaded/photo.jpg",
        mime_type="image/jpeg",
        width=100,
        height=100,
    )

    RoutedSceneAnalyzer(curated, uploaded).analyze(session, asset, {}, {})

    curated.analyze.assert_called_once()
    uploaded.analyze.assert_not_called()
