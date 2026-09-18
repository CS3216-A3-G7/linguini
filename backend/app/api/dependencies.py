"""FastAPI wiring for incremental migration from JSON to PostgreSQL."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request

from app.config import DEMO_USERS_PATH, get_demo_user_id
from app.database import get_language_profile_storage, get_user_storage
from app.repositories.implementations.json.journals import JsonJournalRepository
from app.repositories.implementations.json.language_profiles import JsonLanguageProfileRepository
from app.repositories.implementations.json.learning import JsonLearningRepository
from app.repositories.implementations.json.practice import JsonPracticeRepository
from app.repositories.implementations.json.scenes import JsonSceneRepository
from app.repositories.implementations.json.users import JsonUserRepository
from app.repositories.implementations.postgres.language_profiles import (
    PostgresLanguageProfileRepository,
)
from app.repositories.implementations.postgres.users import PostgresUserRepository
from app.repositories.journals import JournalRepository
from app.repositories.language_profiles import LanguageProfileRepository
from app.repositories.learning import LearningRepository
from app.repositories.practice import PracticeRepository
from app.repositories.scenes import SceneRepository
from app.repositories.users import UserRepository
from app.services.journals import JournalService
from app.services.language_profiles import LanguageProfileService
from app.services.learning import LearningService
from app.services.practice import PracticeService
from app.services.scenes import SceneService
from app.services.users import UserService


def get_user_repository(request: Request) -> UserRepository:
    if get_user_storage() == "postgres":
        return PostgresUserRepository(request.app.state.database_engine)
    return JsonUserRepository(DEMO_USERS_PATH)


def get_journal_repository() -> JournalRepository:
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
    repository: Annotated[JournalRepository, Depends(get_journal_repository)],
    users: Annotated[UserService, Depends(get_user_service)],
    profiles: Annotated[LanguageProfileService, Depends(get_language_profile_service)],
) -> JournalService:
    return JournalService(repository, users, profiles)


def get_learning_repository() -> LearningRepository:
    return JsonLearningRepository(DEMO_USERS_PATH.parent)


def get_scene_repository() -> SceneRepository:
    return JsonSceneRepository(DEMO_USERS_PATH.parent / "scenes.json")


def get_scene_service(
    repository: Annotated[SceneRepository, Depends(get_scene_repository)],
) -> SceneService:
    return SceneService(repository)


def get_practice_repository() -> PracticeRepository:
    return JsonPracticeRepository(DEMO_USERS_PATH.parent / "progress.json")


def get_practice_service(
    repository: Annotated[PracticeRepository, Depends(get_practice_repository)],
    users: Annotated[UserService, Depends(get_user_service)],
    profiles: Annotated[LanguageProfileService, Depends(get_language_profile_service)],
    scenes: Annotated[SceneService, Depends(get_scene_service)],
) -> PracticeService:
    return PracticeService(repository, users, profiles, scenes)


def get_learning_service(
    repository: Annotated[LearningRepository, Depends(get_learning_repository)],
    users: Annotated[UserService, Depends(get_user_service)],
) -> LearningService:
    return LearningService(repository, users)
