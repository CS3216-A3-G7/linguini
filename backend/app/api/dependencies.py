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
    PostgresPracticeRepository,
    SessionBackedLearningRepository,
)
from app.repositories.postgres.scene_objects import PostgresSceneObjectRepository
from app.repositories.postgres.scenes import PostgresSceneRepository
from app.repositories.postgres.tasks import PostgresTaskRepository
from app.repositories.postgres.users import PostgresUserRepository
from app.repositories.postgres.vocabulary import PostgresVocabularyRepository
from app.repositories.practice import PracticeRepository
from app.repositories.scenes import SceneRepository
from app.repositories.users import UserRepository
from app.services.image_storage import ImageStorage
from app.services.journals import JournalService
from app.services.language_profiles import LanguageProfileService
from app.services.learning import LearningService
from app.services.media_assets import MediaAssetService
from app.services.practice import PracticeService
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
    )


def get_learning_repository(
    request: Request, demo_user_id: Annotated[UUID, Depends(get_demo_user_id)]
) -> LearningRepository:
    return SessionBackedLearningRepository(
        PostgresPracticeRepository(request.app.state.database_engine, demo_user_id),
        PostgresVocabularyRepository(request.app.state.database_engine),
    )


def get_scene_repository(request: Request) -> SceneRepository:
    return PostgresSceneRepository(request.app.state.database_engine)


def get_media_asset_repository(request: Request) -> MediaAssetRepository:
    return PostgresMediaAssetRepository(request.app.state.database_engine)


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
    )


def get_scene_service(
    repository: Annotated[SceneRepository, Depends(get_scene_repository)],
    media: Annotated[MediaAssetRepository, Depends(get_media_asset_repository)],
) -> SceneService:
    return SceneService(repository, media, get_media_public_base_url(), get_private_media_urls())


def get_practice_repository(
    request: Request, demo_user_id: Annotated[UUID, Depends(get_demo_user_id)]
) -> PracticeRepository:
    return PostgresPracticeRepository(request.app.state.database_engine, demo_user_id)


def get_practice_service(
    request: Request,
    repository: Annotated[PracticeRepository, Depends(get_practice_repository)],
    users: Annotated[UserService, Depends(get_user_service)],
    profiles: Annotated[LanguageProfileService, Depends(get_language_profile_service)],
    scenes: Annotated[SceneService, Depends(get_scene_service)],
) -> PracticeService:
    return PracticeService(
        repository,
        users,
        profiles,
        scenes,
        PostgresSceneObjectRepository(request.app.state.database_engine),
        PostgresTaskRepository(request.app.state.database_engine),
        get_media_asset_repository(request),
    )


def get_task_service(
    request: Request, users: Annotated[UserService, Depends(get_user_service)]
) -> TaskService:
    return TaskService(PostgresTaskRepository(request.app.state.database_engine), users)


def get_learning_service(
    repository: Annotated[LearningRepository, Depends(get_learning_repository)],
    users: Annotated[UserService, Depends(get_user_service)],
) -> LearningService:
    return LearningService(repository, users)
