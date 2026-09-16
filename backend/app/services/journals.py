from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from app.repositories.journals import JournalRepository
from app.schemas.base import utc_now
from app.schemas.journals import (
    Journal,
    JournalDetailResponse,
    JournalRevision,
    JournalTodayContextResponse,
    UpdateJournalRequest,
    UpsertTodayJournalRequest,
)
from app.services.language_profiles import LanguageProfileService
from app.services.users import UserService


class JournalNotFoundError(Exception):
    pass


class JournalConflictError(Exception):
    pass


class JournalService:
    def __init__(
        self, repository: JournalRepository, users: UserService, profiles: LanguageProfileService
    ) -> None:
        self.repository = repository
        self.users = users
        self.profiles = profiles

    def list_entries(self) -> list[JournalDetailResponse]:
        user = self.users.get_current_user()
        return sorted(
            (row for row in self.repository.read() if row.journal.user_id == user.id),
            key=lambda row: row.journal.local_date,
            reverse=True,
        )

    def get_entry(self, journal_id: UUID) -> JournalDetailResponse:
        entry = next((row for row in self.list_entries() if row.journal.id == journal_id), None)
        if entry is None:
            raise JournalNotFoundError("Journal not found.")
        return entry

    def today(self) -> JournalTodayContextResponse:
        user = self.users.get_current_user()
        day = datetime.now(ZoneInfo(user.timezone)).date()
        entry = next((row for row in self.list_entries() if row.journal.local_date == day), None)
        return JournalTodayContextResponse(
            local_date=day, journal=entry.journal if entry else None, can_create=entry is None
        )

    @staticmethod
    def _revision(entry: JournalDetailResponse, content: str) -> JournalRevision:
        latest = entry.revisions[-1] if entry.revisions else None
        if latest is not None and latest.content == content:
            return latest
        revision = JournalRevision(
            journal_id=entry.journal.id,
            revision_number=len(entry.revisions) + 1,
            content=content,
            created_by="user",
        )
        entry.revisions.append(revision)
        entry.journal.current_revision_id = revision.id
        entry.journal.updated_at = utc_now()
        return revision

    def upsert_today(self, request: UpsertTodayJournalRequest) -> Journal:
        user = self.users.get_current_user()
        if not any(
            row.id == request.language_profile_id and row.is_active
            for row in self.profiles.list_profiles()
        ):
            raise JournalConflictError("Choose the active language profile before saving.")
        day = datetime.now(ZoneInfo(user.timezone)).date()

        def change(rows: list[JournalDetailResponse]) -> Journal:
            entry = next(
                (
                    row
                    for row in rows
                    if row.journal.user_id == user.id and row.journal.local_date == day
                ),
                None,
            )
            if entry is None:
                entry = JournalDetailResponse(
                    journal=Journal(
                        user_id=user.id,
                        language_profile_id=request.language_profile_id,
                        local_date=day,
                        timezone=user.timezone,
                    )
                )
                rows.append(entry)
            elif entry.journal.language_profile_id != request.language_profile_id:
                raise JournalConflictError(
                    "Today's journal uses another language. Open it from journal history."
                )
            if request.content is not None:
                entry.journal.title = request.title
                entry.journal.art = request.art
                entry.journal.selected_words = request.selected_words
                self._revision(entry, request.content)
            return entry.journal

        return self.repository.change(change)

    def update(self, journal_id: UUID, request: UpdateJournalRequest) -> Journal:
        user = self.users.get_current_user()

        def change(rows: list[JournalDetailResponse]) -> Journal:
            entry = next(
                (
                    row
                    for row in rows
                    if row.journal.id == journal_id and row.journal.user_id == user.id
                ),
                None,
            )
            if entry is None:
                raise JournalNotFoundError("Journal not found.")
            for field, value in request.model_dump(exclude_unset=True, by_alias=False).items():
                if field != "content" and value is not None:
                    setattr(entry.journal, field, value)
            if request.content is not None:
                self._revision(entry, request.content)
            entry.journal.updated_at = utc_now()
            return entry.journal

        return self.repository.change(change)

    def add_revision(self, journal_id: UUID, content: str) -> JournalRevision:
        journal = self.update(journal_id, UpdateJournalRequest(content=content))
        return next(
            row
            for row in self.get_entry(journal_id).revisions
            if row.id == journal.current_revision_id
        )
