from pathlib import Path
from uuid import UUID

from pydantic import TypeAdapter, ValidationError

from app.repositories.implementations.json.store import JsonStore
from app.repositories.language_profiles import (
    LanguageProfileConflictError,
    LanguageProfileNotFoundError,
    LanguageProfileStorageError,
)
from app.schemas.base import utc_now
from app.schemas.users import LanguageProfile, UpdateLanguageProfileRequest


class JsonLanguageProfileRepository:
    def __init__(self, path: Path) -> None:
        self.store = JsonStore(path, TypeAdapter(list[LanguageProfile]))

    def list_for_user(self, user_id: UUID) -> list[LanguageProfile]:
        try:
            rows = [row for row in self.store.read() if row.user_id == user_id]
            if sum(row.is_active for row in rows) > 1:
                raise LanguageProfileStorageError("Multiple active language profiles.")
            return rows
        except (OSError, UnicodeError, ValidationError) as exc:
            raise LanguageProfileStorageError("Unable to read language profiles.") from exc

    @staticmethod
    def _activate(rows: list[LanguageProfile], profile: LanguageProfile) -> None:
        if profile.is_active:
            for row in rows:
                if row.user_id == profile.user_id and row.id != profile.id and row.is_active:
                    row.is_active = False
                    row.updated_at = utc_now()

    def create(self, profile: LanguageProfile) -> LanguageProfile:
        def change(rows: list[LanguageProfile]) -> LanguageProfile:
            if any(
                row.user_id == profile.user_id
                and row.source_language_code.lower() == profile.source_language_code.lower()
                and row.target_language_code.lower() == profile.target_language_code.lower()
                for row in rows
            ):
                raise LanguageProfileConflictError("This language profile already exists.")
            self._activate(rows, profile)
            rows.append(profile)
            return profile

        try:
            return self.store.update(change)
        except (OSError, UnicodeError, ValidationError) as exc:
            raise LanguageProfileStorageError("Unable to save language profiles.") from exc

    def update(
        self, user_id: UUID, profile_id: UUID, request: UpdateLanguageProfileRequest
    ) -> LanguageProfile:
        def change(rows: list[LanguageProfile]) -> LanguageProfile:
            for index, row in enumerate(rows):
                if row.user_id == user_id and row.id == profile_id:
                    patch = request.model_dump(exclude_unset=True, by_alias=False)
                    patch = {
                        key: value
                        for key, value in patch.items()
                        if value is not None or key == "daily_goal_minutes"
                    }
                    values = row.model_dump(by_alias=False) | patch | {"updated_at": utc_now()}
                    profile = LanguageProfile.model_validate(values)
                    self._activate(rows, profile)
                    rows[index] = profile
                    return profile
            raise LanguageProfileNotFoundError("Language profile not found.")

        try:
            return self.store.update(change)
        except (OSError, UnicodeError, ValidationError) as exc:
            raise LanguageProfileStorageError("Unable to save language profiles.") from exc
