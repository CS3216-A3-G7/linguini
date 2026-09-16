from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.repositories.journals import JournalStorageError
from app.repositories.language_profiles import (
    LanguageProfileConflictError,
    LanguageProfileNotFoundError,
    LanguageProfileStorageError,
)
from app.repositories.learning import LearningStorageError
from app.repositories.practice import PracticeStorageError
from app.repositories.scenes import SceneStorageError
from app.repositories.users import UserRepositoryError
from app.services.journals import JournalConflictError, JournalNotFoundError
from app.services.language_profiles import NoActiveLanguageError
from app.services.learning import InvalidCursorError, ProgressNotFoundError
from app.services.practice import PracticeConflictError, PracticeNotFoundError
from app.services.scenes import SceneNotFoundError
from app.services.users import UserNotFoundError


def register_learning_errors(app: FastAPI) -> None:
    errors = {
        PracticeStorageError: (
            500,
            "practice_storage_error",
            "Unable to load or save practice. Retry the action.",
        ),
        PracticeNotFoundError: (
            404,
            "practice_not_found",
            "Session or scene not found for the active language.",
        ),
        PracticeConflictError: (
            409,
            "practice_conflict",
            "This practice action is not valid for the current session.",
        ),
        JournalStorageError: (500, "journal_storage_error", "Unable to load or save journal data."),
        JournalNotFoundError: (404, "journal_not_found", "Journal not found."),
        JournalConflictError: (
            409,
            "journal_conflict",
            "Today's journal uses another language. "
            "Open it from journal history, or select its language.",
        ),
        LanguageProfileStorageError: (
            500,
            "language_profile_storage_error",
            "Unable to load or save language profiles.",
        ),
        LanguageProfileNotFoundError: (
            404,
            "language_profile_not_found",
            "Language profile not found.",
        ),
        LanguageProfileConflictError: (
            409,
            "language_profile_exists",
            "This language profile already exists.",
        ),
        NoActiveLanguageError: (
            409,
            "no_active_language",
            "Choose a target language in your profile.",
        ),
        SceneStorageError: (500, "scene_storage_error", "Unable to load scene data."),
        SceneNotFoundError: (404, "scene_not_found", "Scene not found."),
        LearningStorageError: (500, "learning_storage_error", "Unable to load learning data."),
        UserRepositoryError: (500, "user_storage_error", "Unable to load demo user data."),
        UserNotFoundError: (404, "user_not_found", "The configured demo user was not found."),
        ProgressNotFoundError: (404, "progress_not_found", "No progress found for this user."),
        InvalidCursorError: (400, "invalid_cursor", "Invalid vocabulary cursor."),
    }

    async def handle_error(request: Request, exc: Exception) -> JSONResponse:
        status, code, message = errors[type(exc)]
        return JSONResponse(
            status_code=status, content={"detail": {"code": code, "message": message}}
        )

    for error_type in errors:
        app.add_exception_handler(error_type, handle_error)
