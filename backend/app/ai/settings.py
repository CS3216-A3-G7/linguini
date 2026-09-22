"""Centralized AI provider/model configuration.

Pure configuration only: loading these models never constructs SDK clients
and never performs network I/O.
"""

import os
from collections.abc import Mapping
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AiMode(StrEnum):
    REAL = "real"
    DEMO = "demo"


class AiProvider(StrEnum):
    OPENAI = "openai"
    GEMINI = "gemini"
    NONE = "none"


class AiFeature(StrEnum):
    SCENE_ANALYSIS = "sceneAnalysis"
    SCENE_TRANSLATION = "sceneTranslation"
    LEARNING_TASK = "learningTask"
    ISPY_CLUE = "ispyClue"
    ISPY_GUESS = "ispyGuess"


class AiConfigurationError(ValueError):
    """Raised when AI environment configuration is invalid."""


class FeatureModelConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    feature: AiFeature
    provider: AiProvider
    model_name: str = ""
    timeout_seconds: float = Field(gt=0)
    max_output_tokens: int | None = Field(default=None, gt=0)
    max_retries: int = Field(default=0, ge=0)


class AiSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: AiMode
    openai_api_key: str = ""
    gemini_api_key: str = ""
    general_api_key: str = ""
    scene_analysis: FeatureModelConfig
    scene_translation: FeatureModelConfig
    learning_task: FeatureModelConfig
    ispy_clue: FeatureModelConfig
    ispy_guess: FeatureModelConfig

    def api_key_for(self, provider: AiProvider) -> str:
        if provider is AiProvider.OPENAI:
            return self.openai_api_key
        if provider is AiProvider.GEMINI:
            return self.gemini_api_key
        return ""

    def is_configured(self, config: FeatureModelConfig) -> bool:
        return (
            config.provider is not AiProvider.NONE
            and bool(config.model_name)
            and bool(self.api_key_for(config.provider))
        )

    def feature(self, feature: AiFeature) -> FeatureModelConfig:
        return getattr(self, _FEATURE_FIELDS[feature])


_FEATURE_FIELDS: dict[AiFeature, str] = {
    feature: feature.name.lower() for feature in AiFeature
}


class _LegacySpec:
    """Legacy environment variable names and defaults for one feature."""

    def __init__(
        self,
        provider_var: str,
        provider_default: str,
        timeout_var: str,
        timeout_default: str,
        model_vars: dict[AiProvider, str],
        model_defaults: dict[AiProvider, str],
    ) -> None:
        self.provider_var = provider_var
        self.provider_default = provider_default
        self.timeout_var = timeout_var
        self.timeout_default = timeout_default
        self.model_vars = model_vars
        self.model_defaults = model_defaults


_LEGACY_SPECS: dict[AiFeature, _LegacySpec] = {
    AiFeature.SCENE_ANALYSIS: _LegacySpec(
        provider_var="SCENE_ANALYSIS_PROVIDER",
        provider_default="gemini",
        timeout_var="SCENE_ANALYSIS_TIMEOUT_SECONDS",
        timeout_default="120",
        model_vars={
            AiProvider.OPENAI: "OPENAI_SCENE_MODEL",
            AiProvider.GEMINI: "GEMINI_SCENE_MODEL",
        },
        model_defaults={AiProvider.OPENAI: "gpt-4o", AiProvider.GEMINI: ""},
    ),
    AiFeature.SCENE_TRANSLATION: _LegacySpec(
        provider_var="TRANSLATION_PROVIDER",
        provider_default="gemini",
        timeout_var="TRANSLATION_TIMEOUT_SECONDS",
        timeout_default="60",
        model_vars={
            AiProvider.OPENAI: "OPENAI_TRANSLATION_MODEL",
            AiProvider.GEMINI: "GEMINI_TRANSLATION_MODEL",
        },
        model_defaults={
            AiProvider.OPENAI: "gpt-4o-mini",
            AiProvider.GEMINI: "gemini-3.5-flash-lite",
        },
    ),
    AiFeature.LEARNING_TASK: _LegacySpec(
        provider_var="LEARNING_TASK_PROVIDER",
        provider_default="openai",
        timeout_var="LEARNING_TASK_TIMEOUT_SECONDS",
        timeout_default="60",
        model_vars={
            AiProvider.OPENAI: "OPENAI_LEARNING_TASK_MODEL",
            AiProvider.GEMINI: "GEMINI_LEARNING_TASK_MODEL",
        },
        model_defaults={
            AiProvider.OPENAI: "gpt-4o-mini",
            AiProvider.GEMINI: "gemini-3.5-flash-lite",
        },
    ),
    AiFeature.ISPY_CLUE: _LegacySpec(
        provider_var="ISPY_CLUE_PROVIDER",
        provider_default="openai",
        timeout_var="ISPY_CLUE_TIMEOUT_SECONDS",
        timeout_default="60",
        model_vars={AiProvider.OPENAI: "OPENAI_ISPY_CLUE_MODEL"},
        model_defaults={AiProvider.OPENAI: "gpt-4o-mini"},
    ),
    AiFeature.ISPY_GUESS: _LegacySpec(
        provider_var="ISPY_GUESS_PROVIDER",
        provider_default="openai",
        timeout_var="ISPY_GUESS_TIMEOUT_SECONDS",
        timeout_default="60",
        model_vars={AiProvider.OPENAI: "OPENAI_ISPY_GUESS_MODEL"},
        model_defaults={AiProvider.OPENAI: "gpt-4o-mini"},
    ),
}

_ALLOWED_PROVIDERS = ", ".join(provider.value for provider in AiProvider)
_ALLOWED_MODES = ", ".join(mode.value for mode in AiMode)


def _read(env: Mapping[str, str], name: str) -> str | None:
    value = env.get(name)
    return value.strip() if value is not None else None


def _parse_provider(env: Mapping[str, str], feature: AiFeature, stem: str) -> AiProvider:
    spec = _LEGACY_SPECS[feature]
    raw = (
        _read(env, f"AI_{stem}_PROVIDER")
        or _read(env, spec.provider_var)
        or spec.provider_default
    ).casefold()
    try:
        return AiProvider(raw)
    except ValueError as exc:
        raise AiConfigurationError(
            f"Invalid provider for {feature.value}: {raw!r} "
            f"(allowed: {_ALLOWED_PROVIDERS})"
        ) from exc


def _parse_float(
    env: Mapping[str, str], feature: AiFeature, stem: str
) -> float:
    spec = _LEGACY_SPECS[feature]
    canonical = f"AI_{stem}_TIMEOUT_SECONDS"
    raw = _read(env, canonical) or _read(env, spec.timeout_var) or spec.timeout_default
    try:
        value = float(raw)
    except ValueError as exc:
        raise AiConfigurationError(
            f"Invalid timeout for {feature.value}: {raw!r} "
            f"({canonical} must be a positive number of seconds)"
        ) from exc
    if value <= 0:
        raise AiConfigurationError(
            f"Invalid timeout for {feature.value}: {raw!r} "
            f"({canonical} must be a positive number of seconds)"
        )
    return value


def _parse_int(
    env: Mapping[str, str], feature: AiFeature, name: str, kind: str
) -> int | None:
    raw = _read(env, name)
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise AiConfigurationError(
            f"Invalid {kind} for {feature.value}: {raw!r} ({name} must be an integer)"
        ) from exc


def _parse_model(
    env: Mapping[str, str], feature: AiFeature, stem: str, provider: AiProvider
) -> str:
    canonical = _read(env, f"AI_{stem}_MODEL")
    if canonical is not None:
        return canonical
    spec = _LEGACY_SPECS[feature]
    legacy_var = spec.model_vars.get(provider)
    if legacy_var is not None:
        legacy = _read(env, legacy_var)
        if legacy is not None:
            return legacy
    return spec.model_defaults.get(provider, "")


def _load_feature(
    env: Mapping[str, str], feature: AiFeature
) -> FeatureModelConfig:
    stem = feature.name
    provider = _parse_provider(env, feature, stem)
    max_retries = _parse_int(env, feature, f"AI_{stem}_MAX_RETRIES", "max retries")
    max_output_tokens = _parse_int(
        env, feature, f"AI_{stem}_MAX_OUTPUT_TOKENS", "max output tokens"
    )
    try:
        return FeatureModelConfig(
            feature=feature,
            provider=provider,
            model_name=_parse_model(env, feature, stem, provider),
            timeout_seconds=_parse_float(env, feature, stem),
            max_output_tokens=max_output_tokens,
            max_retries=0 if max_retries is None else max_retries,
        )
    except ValueError as exc:
        raise AiConfigurationError(
            f"Invalid configuration for {feature.value}: {exc}"
        ) from exc


def load_ai_settings(env: Mapping[str, str] | None = None) -> AiSettings:
    """Load AI settings from ``env`` (defaults to ``os.environ``).

    Pure: reads only the given mapping. Never constructs SDK clients or
    opens sockets.
    """
    if env is None:
        env = os.environ

    raw_mode = (_read(env, "AI_MODE") or AiMode.DEMO.value).casefold()
    try:
        mode = AiMode(raw_mode)
    except ValueError as exc:
        raise AiConfigurationError(
            f"Invalid AI_MODE: {raw_mode!r} (allowed: {_ALLOWED_MODES})"
        ) from exc

    settings = AiSettings(
        mode=mode,
        openai_api_key=_read(env, "AI_OPENAI_API_KEY")
        or _read(env, "OPENAI_API_KEY")
        or "",
        gemini_api_key=_read(env, "AI_GEMINI_API_KEY")
        or _read(env, "GEMINI_API_KEY")
        or "",
        general_api_key=_read(env, "AI_API_KEY") or "",
        **{
            field: _load_feature(env, feature)
            for feature, field in _FEATURE_FIELDS.items()
        },
    )

    if settings.mode is AiMode.REAL:
        problems: list[str] = []
        for feature, field in _FEATURE_FIELDS.items():
            config = getattr(settings, field)
            if config.provider is AiProvider.NONE:
                continue
            stem = feature.name
            if not config.model_name:
                problems.append(
                    f"{feature.value}: missing model name (set AI_{stem}_MODEL)"
                )
            if not settings.api_key_for(config.provider):
                key_var = f"AI_{config.provider.value.upper()}_API_KEY"
                problems.append(
                    f"{feature.value}: missing {config.provider.value} API key "
                    f"(set {key_var})"
                )
        if problems:
            raise AiConfigurationError(
                "AI_MODE=real requires complete AI configuration: "
                + "; ".join(problems)
            )

    return settings
