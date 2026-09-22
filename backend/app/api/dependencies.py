"""FastAPI wiring for PostgreSQL persistence and the read-only scene catalog."""

import os
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request

from app.ai import (
    AiFeature,
    AiProvider,
    AiSettings,
    AITracer,
    NoOpAITracer,
    load_ai_settings,
)
from app.ai.instrumentation import TracedISpyGuessGenerator
from app.ai.scene_analysis import RoutedSceneAnalyzer, UploadedSceneAnalyzer
from app.ai.vision_gemini import GeminiVisionClient
from app.config import get_demo_user_id, get_media_public_base_url, get_private_media_urls
from app.repositories.journals import JournalRepository
from app.repositories.language_profiles import LanguageProfileRepository
from app.repositories.learning import LearningRepository
from app.repositories.media_assets import MediaAssetRepository
from app.repositories.postgres.journals import PostgresJournalRepository
from app.repositories.postgres.language_profiles import (
    PostgresLanguageProfileRepository,
)
from app.repositories.postgres.media_assets import PostgresMediaAssetRepository
from app.repositories.postgres.practice import (
    SessionBackedLearningRepository,
)
from app.repositories.postgres.scenes import PostgresSceneRepository
from app.repositories.postgres.tasks import PostgresTaskRepository
from app.repositories.postgres.users import PostgresUserRepository
from app.repositories.postgres.vocabulary import PostgresVocabularyRepository
from app.repositories.postgres.workflow import PostgresWorkflowRepository
from app.repositories.scenes import SceneRepository
from app.repositories.users import UserRepository
from app.services.gemini_learning_tasks import GeminiLearningTaskGenerator
from app.services.gemini_translation import GeminiSceneTranslator
from app.services.image_derivatives import ImageDerivatives
from app.services.image_storage import ImageStorage
from app.services.journals import JournalService
from app.services.language_profiles import LanguageProfileService
from app.services.learning import LearningService
from app.services.media_assets import MediaAssetService
from app.services.openai_ispy_clues import OpenAIISpyClueGenerator
from app.services.openai_ispy_guess import OpenAIISpyGuessGenerator
from app.services.openai_learning_tasks import OpenAILearningTaskGenerator
from app.services.openai_translation import OpenAISceneTranslator
from app.services.practice import PracticeService
from app.services.scene_analysis import DeterministicSceneAnalyzer
from app.services.scenes import SceneService
from app.services.tasks import TaskService
from app.services.users import UserService
from app.services.vision_model import VisionModelConfig
from app.services.vision_openai import OpenAIVisionClient


def get_user_repository(request: Request) -> UserRepository:
    return PostgresUserRepository(request.app.state.database_engine)


def get_journal_repository(
    request: Request, demo_user_id: Annotated[UUID, Depends(get_demo_user_id)]
) -> JournalRepository:
    return PostgresJournalRepository(request.app.state.database_engine, demo_user_id)


def get_language_profile_repository(request: Request) -> LanguageProfileRepository:
    return PostgresLanguageProfileRepository(request.app.state.database_engine)


def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    demo_user_id: Annotated[UUID, Depends(get_demo_user_id)],
) -> UserService:
    return UserService(repository, demo_user_id)


def get_language_profile_service(
    repository: Annotated[LanguageProfileRepository, Depends(get_language_profile_repository)],
    users: Annotated[UserService, Depends(get_user_service)],
) -> LanguageProfileService:
    return LanguageProfileService(repository, users)


def get_active_language(
    service: Annotated[LanguageProfileService, Depends(get_language_profile_service)],
) -> str:
    return service.active_language()


def get_journal_service(
    request: Request,
    repository: Annotated[JournalRepository, Depends(get_journal_repository)],
    users: Annotated[UserService, Depends(get_user_service)],
    profiles: Annotated[LanguageProfileService, Depends(get_language_profile_service)],
) -> JournalService:
    return JournalService(
        repository,
        users,
        profiles,
        get_media_asset_repository(request),
        get_media_public_base_url(),
        get_private_media_urls(),
        PostgresVocabularyRepository(request.app.state.database_engine),
    )


def get_learning_repository(
    request: Request, demo_user_id: Annotated[UUID, Depends(get_demo_user_id)]
) -> LearningRepository:
    return SessionBackedLearningRepository(
        request.app.state.database_engine,
        demo_user_id,
        PostgresVocabularyRepository(request.app.state.database_engine),
    )


def get_scene_repository(request: Request) -> SceneRepository:
    return PostgresSceneRepository(request.app.state.database_engine)


def get_media_asset_repository(request: Request) -> MediaAssetRepository:
    return PostgresMediaAssetRepository(request.app.state.database_engine)


# One shared derivative cache per process so its LRU survives across requests.
_IMAGE_DERIVATIVES: ImageDerivatives | None = None


def get_image_derivatives() -> ImageDerivatives:
    global _IMAGE_DERIVATIVES
    if _IMAGE_DERIVATIVES is None:
        _IMAGE_DERIVATIVES = ImageDerivatives(
            ImageStorage(
                os.getenv("SUPABASE_URL", "").strip(),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
            )
        )
    return _IMAGE_DERIVATIVES


def get_media_asset_service(
    repository: Annotated[MediaAssetRepository, Depends(get_media_asset_repository)],
    users: Annotated[UserService, Depends(get_user_service)],
) -> MediaAssetService:
    return MediaAssetService(
        repository,
        users,
        ImageStorage(
            os.getenv("SUPABASE_URL", "").strip(),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
        ),
        get_image_derivatives(),
    )


def get_scene_service(
    repository: Annotated[SceneRepository, Depends(get_scene_repository)],
) -> SceneService:
    return SceneService(repository, get_media_public_base_url(), get_private_media_urls())


def get_ai_settings(request: Request) -> AiSettings:
    """AI settings loaded at app startup; falls back to loading on demand."""
    settings = getattr(request.app.state, "ai_settings", None)
    if settings is None:
        settings = load_ai_settings()
    return settings


def get_ai_tracer(request: Request) -> AITracer:
    """Tracer built in the app lifespan; falls back to a no-op."""
    return getattr(request.app.state, "ai_tracer", None) or NoOpAITracer()


def get_ispy_guess_generator(settings: AiSettings, tracer: AITracer | None = None):
    """Build the target-blind I-Spy evaluator used by task generation and attempts."""
    config = settings.feature(AiFeature.ISPY_GUESS)
    if config.provider is AiProvider.NONE:
        return None
    if config.provider is not AiProvider.OPENAI:
        raise ValueError(f"Unsupported ISPY_GUESS_PROVIDER: {config.provider}")
    if not settings.is_configured(config):
        return None
    return TracedISpyGuessGenerator(
        OpenAIISpyGuessGenerator(
            settings.openai_api_key,
            config.model_name,
            timeout_seconds=config.timeout_seconds,
        ),
        tracer or NoOpAITracer(),
        provider=config.provider.value,
        model=config.model_name,
        max_retries=config.max_retries,
    )


def get_practice_repository(
    request: Request, demo_user_id: Annotated[UUID, Depends(get_demo_user_id)]
) -> PostgresWorkflowRepository:
    engine = request.app.state.database_engine
    settings = get_ai_settings(request)
    deterministic = DeterministicSceneAnalyzer(engine)
    openai_key = settings.openai_api_key
    gemini_key = settings.gemini_api_key
    analyzer = deterministic
    storage = ImageStorage(
        os.getenv("SUPABASE_URL", "").strip(),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
    )

    scene_config = settings.feature(AiFeature.SCENE_ANALYSIS)
    tracer = get_ai_tracer(request)
    if scene_config.provider in (AiProvider.OPENAI, AiProvider.GEMINI):
        if not settings.is_configured(scene_config):
            uploaded_analyzer = None
        else:
            vision_config = VisionModelConfig(
                model_name=scene_config.model_name,
                timeout_seconds=scene_config.timeout_seconds,
                max_output_tokens=scene_config.max_output_tokens or 1500,
                max_retries=min(scene_config.max_retries, 1),
            )
            if scene_config.provider is AiProvider.OPENAI:
                uploaded_analyzer = UploadedSceneAnalyzer(
                    storage,
                    OpenAIVisionClient(openai_key, vision_config),
                    vision_config,
                    tracer=tracer,
                    provider=scene_config.provider.value,
                )
            else:
                uploaded_analyzer = UploadedSceneAnalyzer(
                    storage,
                    GeminiVisionClient(gemini_key, vision_config),
                    vision_config,
                    tracer=tracer,
                    provider=scene_config.provider.value,
                )
    elif scene_config.provider is AiProvider.NONE:
        uploaded_analyzer = None
    else:
        raise ValueError(f"Unsupported SCENE_ANALYSIS_PROVIDER: {scene_config.provider}")
    if uploaded_analyzer:
        analyzer = RoutedSceneAnalyzer(deterministic, uploaded_analyzer)

    translation_config = settings.feature(AiFeature.SCENE_TRANSLATION)
    if translation_config.provider is AiProvider.OPENAI:
        translator = (
            OpenAISceneTranslator(
                openai_key,
                translation_config.model_name,
                timeout_seconds=translation_config.timeout_seconds,
            )
            if settings.is_configured(translation_config)
            else None
        )
    elif translation_config.provider is AiProvider.GEMINI:
        translator = (
            GeminiSceneTranslator(
                gemini_key,
                translation_config.model_name,
                timeout_seconds=translation_config.timeout_seconds,
            )
            if settings.is_configured(translation_config)
            else None
        )
    elif translation_config.provider is AiProvider.NONE:
        translator = None
    else:
        raise ValueError(f"Unsupported TRANSLATION_PROVIDER: {translation_config.provider}")

    learning_task_config = settings.feature(AiFeature.LEARNING_TASK)
    if learning_task_config.provider is AiProvider.OPENAI:
        learning_task_generator = (
            OpenAILearningTaskGenerator(
                openai_key,
                learning_task_config.model_name,
                timeout_seconds=learning_task_config.timeout_seconds,
            )
            if settings.is_configured(learning_task_config)
            else None
        )
    elif learning_task_config.provider is AiProvider.GEMINI:
        learning_task_generator = (
            GeminiLearningTaskGenerator(
                gemini_key,
                learning_task_config.model_name,
                timeout_seconds=learning_task_config.timeout_seconds,
            )
            if settings.is_configured(learning_task_config)
            else None
        )
    elif learning_task_config.provider is AiProvider.NONE:
        learning_task_generator = None
    else:
        raise ValueError(
            f"Unsupported LEARNING_TASK_PROVIDER: {learning_task_config.provider}"
        )

    ispy_clue_config = settings.feature(AiFeature.ISPY_CLUE)
    if ispy_clue_config.provider is AiProvider.OPENAI:
        ispy_clue_generator = (
            OpenAIISpyClueGenerator(
                openai_key,
                ispy_clue_config.model_name,
                timeout_seconds=ispy_clue_config.timeout_seconds,
            )
            if settings.is_configured(ispy_clue_config)
            else None
        )
    elif ispy_clue_config.provider is AiProvider.NONE:
        ispy_clue_generator = None
    else:
        raise ValueError(f"Unsupported ISPY_CLUE_PROVIDER: {ispy_clue_config.provider}")
    return PostgresWorkflowRepository(
        engine,
        demo_user_id,
        analyzer=analyzer,
        translator=translator,
        learning_task_generator=learning_task_generator,
        ispy_clue_generator=ispy_clue_generator,
        ispy_guess_generator=get_ispy_guess_generator(
            settings, get_ai_tracer(request)
        ),
        background=getattr(request.app.state, "background_runner", None),
    )


def get_practice_service(
    repository: Annotated[PostgresWorkflowRepository, Depends(get_practice_repository)],
    users: Annotated[UserService, Depends(get_user_service)],
    profiles: Annotated[LanguageProfileService, Depends(get_language_profile_service)],
) -> PracticeService:
    return PracticeService(repository, users, profiles)


def get_task_service(
    request: Request, users: Annotated[UserService, Depends(get_user_service)]
) -> TaskService:
    return TaskService(
        PostgresTaskRepository(request.app.state.database_engine),
        users,
        request.app.state.database_engine,
        ispy_guess_generator=get_ispy_guess_generator(
            get_ai_settings(request), get_ai_tracer(request)
        ),
    )


def get_learning_service(
    repository: Annotated[LearningRepository, Depends(get_learning_repository)],
    users: Annotated[UserService, Depends(get_user_service)],
) -> LearningService:
    return LearningService(repository, users)
