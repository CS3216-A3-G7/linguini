"""Provider-neutral client/service construction from centralized AI settings.

Reads only ``AiSettings`` — providers and models are never chosen anywhere
else. Returns ``None`` for features configured off so callers keep their
deterministic fallbacks.
"""

from __future__ import annotations

from app.ai.features.translation import SceneTranslationService
from app.ai.observability import AITracer
from app.ai.settings import AiFeature, AiProvider, AiSettings
from app.ai.text_gemini import GeminiTextClient
from app.ai.text_model import TextModelClient, TextModelConfig
from app.ai.text_openai import OpenAITextClient


def build_text_client(
    provider: AiProvider, settings: AiSettings, config: TextModelConfig
) -> TextModelClient:
    if provider is AiProvider.OPENAI:
        return OpenAITextClient(settings.openai_api_key, config)
    if provider is AiProvider.GEMINI:
        return GeminiTextClient(settings.gemini_api_key, config)
    raise ValueError(f"unsupported text provider {provider!r}")


def build_scene_translator(
    settings: AiSettings, tracer: AITracer
) -> SceneTranslationService | None:
    """Build the configured scene translator, or ``None`` when turned off.

    ``None`` preserves the workflow's deterministic offline fallback.
    """
    config = settings.feature(AiFeature.SCENE_TRANSLATION)
    if config.provider is AiProvider.NONE or not settings.is_configured(config):
        return None
    text_config = TextModelConfig(
        model_name=config.model_name,
        timeout_seconds=config.timeout_seconds,
        max_output_tokens=config.max_output_tokens or 1500,
        max_retries=min(config.max_retries, 1),
    )
    client = build_text_client(config.provider, settings, text_config)
    return SceneTranslationService(
        client, text_config, tracer=tracer, provider=config.provider.value
    )
