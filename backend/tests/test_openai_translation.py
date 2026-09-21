from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.schemas.translation import SceneTranslationResult
from app.services.openai_translation import OpenAISceneTranslator
from app.services.scene_translation import SceneTranslationError

INPUT = {
    "targetLanguage": "fr",
    "sceneTitle": "Desk",
    "sceneSummary": "A red cup is on a table.",
    "objects": [{"key": "object_1", "source": "cup"}],
    "attributes": [{"key": "object_1:color", "source": "red"}],
    "relationships": [{"key": "relation_1", "source": "on"}],
}


def translator(tmp_path: Path, result: SceneTranslationResult | None):
    prompt = tmp_path / "translation.txt"
    prompt.write_text("Translate exactly.", encoding="utf-8")
    client = SimpleNamespace(
        responses=SimpleNamespace(
            parse=MagicMock(return_value=SimpleNamespace(output_parsed=result))
        )
    )
    return OpenAISceneTranslator(
        "test-key", "test-model", client=client, prompt_path=prompt
    ), client


def test_openai_translation_uses_shared_structured_contract(tmp_path):
    expected = SceneTranslationResult.model_validate(
        {
            "objects": [
                {
                    "key": "object_1",
                    "source": "cup",
                    "translation": "tasse",
                    "article": "la",
                    "gender": "feminine",
                }
            ],
            "attributes": [
                {"key": "object_1:color", "source": "red", "translation": "rouge"}
            ],
            "relationships": [
                {"key": "relation_1", "source": "on", "translation": "sur"}
            ],
        }
    )
    provider, client = translator(tmp_path, expected)

    result = provider.translate(INPUT)

    assert result == expected
    call = client.responses.parse.call_args.kwargs
    assert call["text_format"] is SceneTranslationResult
    assert call["model"] == "test-model"


def test_openai_translation_rejects_an_empty_response(tmp_path):
    provider, _ = translator(tmp_path, None)

    with pytest.raises(SceneTranslationError):
        provider.translate(INPUT)
