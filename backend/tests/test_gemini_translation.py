from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.gemini_translation import GeminiSceneTranslator, SceneTranslationError


def translator(tmp_path: Path, payload: str):
    prompt = tmp_path / "translation.txt"
    prompt.write_text("Translate exactly.", encoding="utf-8")
    client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=MagicMock(return_value=SimpleNamespace(text=payload))
        )
    )
    return GeminiSceneTranslator(
        "test-key", "test-model", client=client, prompt_path=prompt
    ), client


INPUT = {
    "targetLanguage": "es",
    "sceneTitle": "Desk",
    "sceneSummary": "A red cup is on a table.",
    "objects": [{"key": "object_1", "source": "cup"}],
    "attributes": [{"key": "object_1:color", "source": "red"}],
    "relationships": [{"key": "relation_1", "source": "on"}],
}


def test_translation_preserves_terms_and_returns_translations(tmp_path):
    provider, client = translator(
        tmp_path,
        '{"objects":[{"key":"object_1","source":"cup","translation":"taza","article":"la","gender":"feminine"}],'
        '"attributes":[{"key":"object_1:color","source":"red","translation":"rojo"}],'
        '"relationships":[{"key":"relation_1","source":"on","translation":"sobre"}]}',
    )

    result = provider.translate(INPUT)

    assert result.objects[0].translation == "taza"
    assert result.attributes[0].translation == "rojo"
    assert result.relationships[0].translation == "sobre"
    assert client.models.generate_content.call_count == 1


def test_translation_rejects_changed_or_missing_terms(tmp_path):
    provider, _ = translator(
        tmp_path,
        '{"objects":[{"key":"object_1","source":"mug","translation":"taza"}],'
        '"attributes":[],"relationships":[]}',
    )

    with pytest.raises(SceneTranslationError):
        provider.translate(INPUT)
