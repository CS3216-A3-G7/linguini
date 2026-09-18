"""FastAPI wiring for incremental migration from JSON to PostgreSQL."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request

from app.api.errors import service_not_implemented
from app.config import DEMO_USERS_PATH, get_demo_user_id
from app.database import (
    get_journal_storage,
    get_language_profile_storage,
    get_media_asset_storage,
    get_session_storage,
    get_user_storage,
    get_vocabulary_storage,
)
from app.repositories.implementations.json.journals import JsonJournalRepository
from app.repositories.implementations.json.language_profiles import JsonLanguageProfileRepository
from app.repositories.implementations.json.learning import JsonLearningRepository
from app.repositories.implementations.json.media_assets import JsonMediaAssetRepository
from app.repositories.implementations.json.practice import JsonPracticeRepository
from app.repositories.implementations.json.scenes import JsonSceneRepository
from app.repositories.implementations.json.users import JsonUserRepository
from app.repositories.implementations.postgres.journals import PostgresJournalRepository
from app.repositories.implementations.postgres.language_profiles import (
    PostgresLanguageProfileRepository,
)
from app.repositories.implementations.postgres.media_assets import PostgresMediaAssetRepository
from app.repositories.implementations.postgres.practice import (
    PostgresPracticeRepository,
    SessionBackedLearningRepository,
)
from app.repositories.implementations.postgres.scene_objects import PostgresSceneObjectRepository
from app.repositories.implementations.postgres.tasks import PostgresTaskRepository
from app.repositories.implementations.postgres.users import PostgresUserRepository
from app.repositories.implementations.postgres.vocabulary import PostgresVocabularyRepository
from app.repositories.journals import JournalRepository
from app.repositories.language_profiles import LanguageProfileRepository
from app.repositories.learning import LearningRepository
from app.repositories.media_assets import MediaAssetRepository
from app.repositories.practice import PracticeRepository
from app.repositories.scenes import SceneRepository
from app.repositories.users import UserRepository
from app.services.journals import JournalService
from app.services.language_profiles import LanguageProfileService
from app.services.learning import LearningService
from app.services.media_assets import MediaAssetService
from app.services.practice import PracticeService
from app.services.scenes import SceneService
from app.services.tasks import TaskService
from app.services.users import UserService


def get_user_repository(request: Request) -> UserRepository:
    if get_user_storage() == "postgres":
        return PostgresUserRepository(request.app.state.database_engine)
    return JsonUserRepository(DEMO_USERS_PATH)


def get_journal_repository(
    request: Request, demo_user_id: Annotated[UUID, Depends(get_demo_user_id)]
) -> JournalRepository:
    if get_journal_storage() == "postgres":
        return PostgresJournalRepository(request.app.state.database_engine, demo_user_id)
    return JsonJournalRepository(DEMO_USERS_PATH.parent / "journals.json")


def get_language_profile_repository(request: Request) -> LanguageProfileRepository:
    if get_language_profile_storage() == "postgres":
        return PostgresLanguageProfileRepository(request.app.state.database_engine)
    return JsonLanguageProfileRepository(DEMO_USERS_PATH.parent / "language_profiles.json")


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
    return JournalService(repository, users, profiles, get_media_asset_repository(request))


def get_learning_repository(
    request: Request, demo_user_id: Annotated[UUID, Depends(get_demo_user_id)]
) -> LearningRepository:
    json_repository = JsonLearningRepository(DEMO_USERS_PATH.parent)
    if get_vocabulary_storage() == "postgres":
        json_repository = PostgresVocabularyRepository(
            request.app.state.database_engine, json_repository
        )
    if get_session_storage() == "postgres":
        return SessionBackedLearningRepository(
            PostgresPracticeRepository(request.app.state.database_engine, demo_user_id),
            json_repository,
        )
    return json_repository


def get_scene_repository() -> SceneRepository:
    return JsonSceneRepository(DEMO_USERS_PATH.parent / "scenes.json")


def get_media_asset_repository(request: Request) -> MediaAssetRepository:
    if get_media_asset_storage() == "postgres":
        return PostgresMediaAssetRepository(request.app.state.database_engine)
    return JsonMediaAssetRepository(DEMO_USERS_PATH.parent / "scenes.json")


def get_media_asset_service(
    repository: Annotated[MediaAssetRepository, Depends(get_media_asset_repository)],
    users: Annotated[UserService, Depends(get_user_service)],
) -> MediaAssetService:
    return MediaAssetService(repository, users)


def get_scene_service(
    repository: Annotated[SceneRepository, Depends(get_scene_repository)],
    media: Annotated[MediaAssetRepository, Depends(get_media_asset_repository)],
) -> SceneService:
    return SceneService(repository, media if get_media_asset_storage() == "postgres" else None)


def get_practice_repository(
    request: Request, demo_user_id: Annotated[UUID, Depends(get_demo_user_id)]
) -> PracticeRepository:
    if get_session_storage() == "postgres":
        return PostgresPracticeRepository(request.app.state.database_engine, demo_user_id)
    return JsonPracticeRepository(DEMO_USERS_PATH.parent / "progress.json")


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
        PostgresSceneObjectRepository(request.app.state.database_engine)
        if get_session_storage() == "postgres"
        else None,
        PostgresTaskRepository(request.app.state.database_engine)
        if get_session_storage() == "postgres"
        else None,
    )


def get_task_service(
    request: Request, users: Annotated[UserService, Depends(get_user_service)]
) -> TaskService:
    if get_session_storage() != "postgres":
        service_not_implemented("Task storage requires PostgreSQL session storage")
    return TaskService(PostgresTaskRepository(request.app.state.database_engine), users)


def get_learning_service(
    repository: Annotated[LearningRepository, Depends(get_learning_repository)],
    users: Annotated[UserService, Depends(get_user_service)],
) -> LearningService:
    return LearningService(repository, users)
