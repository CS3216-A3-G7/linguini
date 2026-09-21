from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from app.repositories.journals import (
    FutureJournalDateError,
    JournalConflictError,
    JournalNotFoundError,
    JournalRepository,
)
from app.repositories.media_assets import MediaAssetRepository, SessionImage
from app.schemas.base import utc_now
from app.schemas.enums import JournalStatus, JournalSuggestionStatus, MediaSource, MediaType
from app.schemas.journals import (
    AddJournalMediaRequest,
    Journal,
    JournalDetailResponse,
    JournalMedia,
    JournalPhotoOption,
    JournalRevision,
    JournalSuggestion,
    JournalTodayContextResponse,
    UpdateJournalRequest,
    UpsertTodayJournalRequest,
)
from app.services.language_profiles import LanguageProfileService
from app.services.media_urls import PrivateMediaUrls, public_media_url
from app.services.users import UserService

THUMBNAIL_WIDTH = 400
DETAIL_WIDTH = 1200


class JournalService:
    def __init__(
        self,
        repository: JournalRepository,
        users: UserService,
        profiles: LanguageProfileService,
        media: MediaAssetRepository | None = None,
        media_public_base_url: str | None = None,
        private_media_urls: PrivateMediaUrls | None = None,
    ) -> None:
        self.repository = repository
        self.users = users
        self.profiles = profiles
        self.media = media
        self.media_public_base_url = media_public_base_url
        self.private_media_urls = private_media_urls

    def _with_images(
        self, rows: list[JournalDetailResponse], *, cover_width: int | None = None
    ) -> list[JournalDetailResponse]:
        covers = {
            row.journal.id: min(row.media, key=lambda media: media.display_order).media_asset_id
            for row in rows
            if row.media
        }
        assets = self.media.get_by_ids(list(covers.values())) if self.media and covers else {}
        keys = {}
        for row in rows:
            asset = assets.get(covers.get(row.journal.id))
            if (
                asset
                and asset.media_type == MediaType.IMAGE
                and (
                    asset.owner_user_id == row.journal.user_id
                    or asset.source == MediaSource.PRELOADED
                )
            ):
                keys[row.journal.id] = asset.storage_key
        urls = (
            (
                self.private_media_urls.resolve(list(keys.values()), width=cover_width)
                if cover_width is not None
                else self.private_media_urls.resolve(list(keys.values()))
            )
            if self.private_media_urls
            else {key: public_media_url(key, self.media_public_base_url) for key in keys.values()}
        )
        return [
            row.model_copy(update={"image_url": urls.get(keys.get(row.journal.id))}) for row in rows
        ]

    def _with_media(self, entry: JournalDetailResponse) -> JournalDetailResponse:
        """Hydrate every attached photo, never mutating the repository's rows."""
        assets = (
            self.media.get_by_ids([media.media_asset_id for media in entry.media])
            if self.media is not None and entry.media
            else {}
        )
        allowed = {
            media.media_asset_id: asset
            for media in entry.media
            if (asset := assets.get(media.media_asset_id)) is not None
            and asset.media_type == MediaType.IMAGE
            and (
                asset.owner_user_id == entry.journal.user_id
                or asset.source == MediaSource.PRELOADED
            )
        }
        keys = [asset.storage_key for asset in allowed.values()]
        urls = (
            self.private_media_urls.resolve(keys, width=DETAIL_WIDTH)
            if self.private_media_urls
            else {key: public_media_url(key, self.media_public_base_url) for key in keys}
        )
        media = []
        for row in entry.media:
            asset = allowed.get(row.media_asset_id)
            media.append(
                row.model_copy(
                    update={
                        "image_url": urls.get(asset.storage_key) if asset else None,
                        "width": asset.width if asset else None,
                        "height": asset.height if asset else None,
                    }
                )
            )
        cover = min(media, key=lambda row: row.display_order) if media else None
        cover_url = (
            urls.get(allowed[cover.media_asset_id].storage_key)
            if cover is not None and cover.media_asset_id in allowed
            else None
        )
        return entry.model_copy(update={"media": media, "image_url": cover_url})

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
        return self._with_images(
            sorted(
                (row for row in self.repository.read() if row.journal.user_id == user.id),
                key=lambda row: row.journal.local_date,
                reverse=True,
            ),
            cover_width=THUMBNAIL_WIDTH,
        )

    def get_entry(self, journal_id: UUID) -> JournalDetailResponse:
        user = self.users.get_current_user()
        entry = self._find(self.repository.read(), journal_id, user.id)
        return self._with_media(entry)

    def today(self) -> JournalTodayContextResponse:
        return self.day_context(None)

    def day_context(self, day: date | None = None) -> JournalTodayContextResponse:
        user = self.users.get_current_user()
        tz = ZoneInfo(user.timezone)
        today = datetime.now(tz).date()
        day = day or today
        if day > today:
            raise FutureJournalDateError("Cannot create a journal entry for a future date.")
        # Look up the day's entry without hydrating media; only eligible photos
        # need signed URLs here, so list_entries' cover signing would be wasted.
        entry = next(
            (
                row
                for row in self.repository.read()
                if row.journal.user_id == user.id and row.journal.local_date == day
            ),
            None,
        )
        eligible_photos: list[JournalPhotoOption] = []
        if self.media is not None:
            start = datetime.combine(day, time.min, tzinfo=tz)
            end = start + timedelta(days=1)
            unique: dict[UUID, SessionImage] = {}
            for image in self.media.list_completed_session_images(user.id, start, end):
                unique.setdefault(image.asset.id, image)
            images = list(unique.values())
            keys = [image.asset.storage_key for image in images]
            urls = (
                self.private_media_urls.resolve(keys, width=THUMBNAIL_WIDTH)
                if self.private_media_urls
                else {key: public_media_url(key, self.media_public_base_url) for key in keys}
            )
            eligible_photos = [
                JournalPhotoOption(
                    media_asset_id=image.asset.id,
                    image_url=urls.get(image.asset.storage_key),
                    width=image.asset.width,
                    height=image.asset.height,
                    session_id=image.session_id,
                    completed_at=image.completed_at,
                )
                for image in images
            ]
        return JournalTodayContextResponse(
            local_date=day,
            journal=entry.journal if entry else None,
            eligible_photos=eligible_photos,
            can_create=entry is None,
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

    @staticmethod
    def _set_cover(entry: JournalDetailResponse, asset_id: UUID | None) -> None:
        cover = min(entry.media, key=lambda row: row.display_order, default=None)
        if cover is not None and cover.media_asset_id == asset_id:
            return
        order = cover.display_order if cover else 0
        if cover:
            entry.media.remove(cover)
        if asset_id is not None:
            existing = next((row for row in entry.media if row.media_asset_id == asset_id), None)
            if existing:
                existing.display_order = order
            else:
                entry.media.append(
                    JournalMedia(
                        journal_id=entry.journal.id,
                        media_asset_id=asset_id,
                        display_order=order,
                    )
                )

    def upsert_today(self, request: UpsertTodayJournalRequest) -> Journal:
        return self.upsert(request, None)

    def upsert(self, request: UpsertTodayJournalRequest, day: date | None = None) -> Journal:
        user = self.users.get_current_user()
        today = datetime.now(ZoneInfo(user.timezone)).date()
        day = day or today
        if day > today:
            raise FutureJournalDateError("Cannot create a journal entry for a future date.")
        if request.media_asset_id is not None:
            self._check_media(request.media_asset_id, user.id, MediaType.IMAGE)
        if not any(
            row.id == request.language_profile_id and row.is_active
            for row in self.profiles.list_profiles()
        ):
            raise JournalConflictError("Choose the active language profile before saving.")

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
                    "That day's journal uses another language. Open it from journal history."
                )
            if request.content is not None:
                entry.journal.title = request.title
                entry.journal.selected_words = request.selected_words
                self._revision(entry, request.content)
            if "media_asset_id" in request.model_fields_set:
                self._set_cover(entry, request.media_asset_id)
            return entry.journal

        return self.repository.change(change)

    def update(self, journal_id: UUID, request: UpdateJournalRequest) -> Journal:
        user = self.users.get_current_user()
        if request.media_asset_id is not None:
            self._check_media(request.media_asset_id, user.id, MediaType.IMAGE)
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
                if field not in ("content", "media_asset_id") and (
                    value is not None or field == "audio_media_asset_id"
                ):
                    setattr(entry.journal, field, value)
            if request.content is not None:
                self._revision(entry, request.content)
            if "media_asset_id" in request.model_fields_set:
                self._set_cover(entry, request.media_asset_id)
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
