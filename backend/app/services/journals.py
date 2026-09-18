from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from app.repositories.journals import JournalConflictError, JournalNotFoundError, JournalRepository
from app.repositories.media_assets import MediaAssetRepository
from app.schemas.base import utc_now
from app.schemas.enums import JournalStatus, JournalSuggestionStatus, MediaSource, MediaType
from app.schemas.journals import (
    AddJournalMediaRequest,
    Journal,
    JournalDetailResponse,
    JournalMedia,
    JournalRevision,
    JournalSuggestion,
    JournalTodayContextResponse,
    UpdateJournalRequest,
    UpsertTodayJournalRequest,
)
from app.services.language_profiles import LanguageProfileService
from app.services.users import UserService


class JournalService:
    def __init__(
        self,
        repository: JournalRepository,
        users: UserService,
        profiles: LanguageProfileService,
        media: MediaAssetRepository | None = None,
    ) -> None:
        self.repository = repository
        self.users = users
        self.profiles = profiles
        self.media = media

    @staticmethod
    def _find(rows, journal_id, user_id):
        entry = next(
            (
                row
                for row in rows
                if row.journal.id == journal_id and row.journal.user_id == user_id
            ),
            None,
        )
        if entry is None:
            raise JournalNotFoundError("Journal not found.")
        return entry

    def _check_media(self, asset_id: UUID, user_id: UUID, media_type: MediaType) -> None:
        asset = self.media.get_by_ids([asset_id]).get(asset_id) if self.media is not None else None
        if (
            asset is None
            or asset.media_type != media_type
            or not (
                asset.owner_user_id == user_id
                or media_type == MediaType.IMAGE
                and asset.source == MediaSource.PRELOADED
            )
        ):
            raise JournalConflictError(
                "Journal media is missing, inaccessible or has the wrong type."
            )

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
    def _revision(entry: JournalDetailResponse, content: str, created_by="user") -> JournalRevision:
        latest = next(
            (row for row in entry.revisions if row.id == entry.journal.current_revision_id), None
        )
        if latest is not None and latest.content == content:
            return latest
        revision = JournalRevision(
            journal_id=entry.journal.id,
            revision_number=max((row.revision_number for row in entry.revisions), default=0) + 1,
            content=content,
            created_by=created_by,
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
        if request.audio_media_asset_id is not None:
            self._check_media(request.audio_media_asset_id, user.id, MediaType.AUDIO)

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
                if field != "content" and (value is not None or field == "audio_media_asset_id"):
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

    def add_media(self, journal_id: UUID, request: AddJournalMediaRequest) -> JournalMedia:
        user = self.users.get_current_user()
        self._check_media(request.media_asset_id, user.id, MediaType.IMAGE)

        def change(rows):
            entry = self._find(rows, journal_id, user.id)
            existing = next(
                (row for row in entry.media if row.media_asset_id == request.media_asset_id), None
            )
            if existing is not None:
                if (
                    existing.display_order != request.display_order
                    or existing.caption != request.caption
                ):
                    raise JournalConflictError("Photo already attached with different metadata.")
                return existing
            if any(row.display_order == request.display_order for row in entry.media):
                raise JournalConflictError("Photo position is occupied.")
            media = JournalMedia(journal_id=journal_id, **request.model_dump(by_alias=False))
            entry.media.append(media)
            entry.journal.updated_at = utc_now()
            return media

        return self.repository.change(change)

    def remove_media(self, journal_id: UUID, media_asset_id: UUID) -> None:
        user = self.users.get_current_user()

        def change(rows):
            entry = self._find(rows, journal_id, user.id)
            if any(row.media_asset_id == media_asset_id for row in entry.media):
                entry.media = [row for row in entry.media if row.media_asset_id != media_asset_id]
                entry.journal.updated_at = utc_now()

        self.repository.change(change)

    def complete(self, journal_id: UUID, revision_id: UUID) -> Journal:
        user = self.users.get_current_user()

        def change(rows):
            entry = self._find(rows, journal_id, user.id)
            if not any(row.id == revision_id for row in entry.revisions):
                raise JournalConflictError("Revision does not belong to this journal.")
            if (
                entry.journal.status == JournalStatus.COMPLETED
                and entry.journal.current_revision_id == revision_id
            ):
                return entry.journal
            entry.journal.current_revision_id = revision_id
            entry.journal.completed_at = utc_now()
            entry.journal.status = JournalStatus.COMPLETED
            entry.journal.updated_at = utc_now()
            return entry.journal

        return self.repository.change(change)

    def review_suggestion(self, suggestion_id: UUID, *, accept: bool) -> JournalSuggestion:
        user = self.users.get_current_user()

        def change(rows):
            pair = next(
                (
                    (entry, suggestion)
                    for entry in rows
                    if entry.journal.user_id == user.id
                    for suggestion in entry.suggestions
                    if suggestion.id == suggestion_id
                ),
                None,
            )
            if pair is None:
                raise JournalNotFoundError("Suggestion not found.")
            entry, suggestion = pair
            status = (
                JournalSuggestionStatus.ACCEPTED if accept else JournalSuggestionStatus.REJECTED
            )
            if suggestion.status == status:
                return suggestion
            if suggestion.status != JournalSuggestionStatus.PENDING:
                raise JournalConflictError("Suggestion has already been reviewed.")
            if accept:
                if entry.journal.current_revision_id != suggestion.base_revision_id:
                    raise JournalConflictError(
                        "Suggestion is stale; request feedback for the current revision."
                    )
                base = next(row for row in entry.revisions if row.id == suggestion.base_revision_id)
                if (
                    base.content[suggestion.start_offset : suggestion.end_offset]
                    != suggestion.original_text
                ):
                    raise JournalConflictError("Suggestion no longer matches its revision.")
                content = (
                    base.content[: suggestion.start_offset]
                    + suggestion.suggested_text
                    + base.content[suggestion.end_offset :]
                )
                if len(content) > 20_000:
                    raise JournalConflictError(
                        "Accepted suggestion would exceed the journal length limit."
                    )
                self._revision(entry, content, created_by="merged")
            suggestion.status = status
            suggestion.updated_at = utc_now()
            return suggestion

        return self.repository.change(change)
