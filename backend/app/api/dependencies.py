"""FastAPI wiring for PostgreSQL persistence and the read-only scene catalog."""

import os
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request

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
from app.services.gemini_scene_analysis import GeminiSceneAnalyzer, RoutedSceneAnalyzer
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
from app.services.openai_scene_analysis import OpenAISceneAnalyzer
from app.services.openai_translation import OpenAISceneTranslator
from app.services.practice import PracticeService
from app.services.scene_analysis import DeterministicSceneAnalyzer
from app.services.scenes import SceneService
from app.services.tasks import TaskService
from app.services.users import UserService


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


def get_ispy_guess_generator():
    """Build the target-blind I-Spy evaluator used by task generation and attempts."""
    provider = os.getenv("ISPY_GUESS_PROVIDER", "openai").strip().casefold()
    if provider == "none":
        return None
    if provider != "openai":
        raise ValueError(f"Unsupported ISPY_GUESS_PROVIDER: {provider}")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_ISPY_GUESS_MODEL", "gpt-4o-mini").strip()
    if not api_key or not model:
        return None
    return OpenAIISpyGuessGenerator(
        api_key,
        model,
        timeout_seconds=int(os.getenv("ISPY_GUESS_TIMEOUT_SECONDS", "60")),
    )


def get_practice_repository(
    request: Request, demo_user_id: Annotated[UUID, Depends(get_demo_user_id)]
) -> PostgresWorkflowRepository:
    engine = request.app.state.database_engine
    deterministic = DeterministicSceneAnalyzer(engine)
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    scene_provider = os.getenv("SCENE_ANALYSIS_PROVIDER", "gemini").strip().casefold()
    scene_timeout = int(os.getenv("SCENE_ANALYSIS_TIMEOUT_SECONDS", "120").strip())
    translation_provider = os.getenv("TRANSLATION_PROVIDER", "gemini").strip().casefold()
    analyzer = deterministic
    storage = ImageStorage(
        os.getenv("SUPABASE_URL", "").strip(),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
    )
    if scene_provider == "openai":
        openai_scene_model = os.getenv("OPENAI_SCENE_MODEL", "gpt-4o").strip()
        uploaded_analyzer = (
            OpenAISceneAnalyzer(
                storage,
                openai_key,
                openai_scene_model,
                timeout_seconds=scene_timeout,
            )
            if openai_key and openai_scene_model
            else None
        )
    elif scene_provider == "gemini":
        gemini_model = os.getenv("GEMINI_SCENE_MODEL", "").strip()
        uploaded_analyzer = (
            GeminiSceneAnalyzer(
                storage,
                gemini_key,
                gemini_model,
                timeout_seconds=scene_timeout,
            )
            if gemini_key and gemini_model
            else None
        )
    else:
        raise ValueError(f"Unsupported SCENE_ANALYSIS_PROVIDER: {scene_provider}")
    if uploaded_analyzer:
        analyzer = RoutedSceneAnalyzer(deterministic, uploaded_analyzer)

    translation_timeout = int(os.getenv("TRANSLATION_TIMEOUT_SECONDS", "60"))
    if translation_provider == "openai":
        openai_model = os.getenv("OPENAI_TRANSLATION_MODEL", "gpt-4o-mini").strip()
        translator = (
            OpenAISceneTranslator(
                openai_key,
                openai_model,
                timeout_seconds=translation_timeout,
            )
            if openai_key and openai_model
            else None
        )
    elif translation_provider == "gemini":
        translation_model = os.getenv(
            "GEMINI_TRANSLATION_MODEL", "gemini-3.5-flash-lite"
        ).strip()
        translator = (
            GeminiSceneTranslator(
                gemini_key,
                translation_model,
                timeout_seconds=translation_timeout,
            )
            if gemini_key and translation_model
            else None
        )
    else:
        raise ValueError(f"Unsupported TRANSLATION_PROVIDER: {translation_provider}")

    learning_task_provider = os.getenv("LEARNING_TASK_PROVIDER", "openai").strip().casefold()
    learning_task_timeout = int(os.getenv("LEARNING_TASK_TIMEOUT_SECONDS", "60"))
    if learning_task_provider == "openai":
        openai_learning_model = os.getenv("OPENAI_LEARNING_TASK_MODEL", "gpt-4o-mini").strip()
        learning_task_generator = (
            OpenAILearningTaskGenerator(
                openai_key,
                openai_learning_model,
                timeout_seconds=learning_task_timeout,
            )
            if openai_key and openai_learning_model
            else None
        )
    elif learning_task_provider == "gemini":
        gemini_learning_model = os.getenv(
            "GEMINI_LEARNING_TASK_MODEL", "gemini-3.5-flash-lite"
        ).strip()
        learning_task_generator = (
            GeminiLearningTaskGenerator(
                gemini_key,
                gemini_learning_model,
                timeout_seconds=learning_task_timeout,
            )
            if gemini_key and gemini_learning_model
            else None
        )
    else:
        raise ValueError(f"Unsupported LEARNING_TASK_PROVIDER: {learning_task_provider}")
    ispy_clue_provider = os.getenv("ISPY_CLUE_PROVIDER", "openai").strip().casefold()
    ispy_clue_timeout = int(os.getenv("ISPY_CLUE_TIMEOUT_SECONDS", "60"))
    if ispy_clue_provider == "openai":
        ispy_clue_model = os.getenv("OPENAI_ISPY_CLUE_MODEL", "gpt-4o-mini").strip()
        ispy_clue_generator = (
            OpenAIISpyClueGenerator(
                openai_key, ispy_clue_model, timeout_seconds=ispy_clue_timeout
            )
            if openai_key and ispy_clue_model
            else None
        )
    elif ispy_clue_provider == "none":
        ispy_clue_generator = None
    else:
        raise ValueError(f"Unsupported ISPY_CLUE_PROVIDER: {ispy_clue_provider}")
    return PostgresWorkflowRepository(
        engine,
        demo_user_id,
        analyzer=analyzer,
        translator=translator,
        learning_task_generator=learning_task_generator,
        ispy_clue_generator=ispy_clue_generator,
        ispy_guess_generator=get_ispy_guess_generator(),
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
        ispy_guess_generator=get_ispy_guess_generator(),
    )


def get_learning_service(
    repository: Annotated[LearningRepository, Depends(get_learning_repository)],
    users: Annotated[UserService, Depends(get_user_service)],
) -> LearningService:
    return LearningService(repository, users)
