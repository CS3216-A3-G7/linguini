"""Atomic normalized session workflow. Locks serialize each user's transitions."""

from contextlib import contextmanager
from datetime import timedelta
from uuid import uuid5

from sqlalchemy import DateTime, and_, case, delete, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as upsert
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.postgres.language_profiles import language_profiles
from app.repositories.postgres.media_assets import media_assets
from app.repositories.postgres.practice import sessions
from app.repositories.postgres.scene_objects import (
    object_values,
    scene_object_relations,
    scene_objects,
)
from app.repositories.postgres.scenes import preloaded_scenes
from app.repositories.postgres.tasks import entity_values, session_tasks, task_attempts
from app.repositories.postgres.users import users
from app.repositories.postgres.vocabulary import (
    user_vocabulary_progress,
    vocabulary_encounters,
    vocabulary_items,
    vocabulary_translations,
)
from app.repositories.practice import (
    ActiveSessionExistsError,
    PracticeConflictError,
    PracticeNotFoundError,
    PracticeStorageError,
)
from app.schemas.base import utc_now
from app.schemas.enums import SessionStatus
from app.schemas.media import MediaAsset, SceneObject, SceneObjectRelation
from app.schemas.sessions import (
    Session,
    SessionDetailResponse,
    SessionStatusResponse,
    SessionSummaryResponse,
)
from app.schemas.tasks import (
    SessionProgress,
    SessionTask,
    SessionTaskPublic,
    TaskActionResponse,
    TaskAttempt,
)
from app.schemas.vocabulary import (
    UserVocabularyProgress,
    VocabularyEncounter,
    VocabularyItem,
    VocabularyTranslation,
)
from app.services.media_urls import MediaUrlError, PrivateMediaUrls, public_media_url
from app.services.scene_analysis import DeterministicSceneAnalyzer, SceneAnalysisError
from app.services.session_plan import build_tasks

TERMINAL = {"completed", "abandoned", "failed"}
ALLOWED_TRANSITIONS = {
    "created": {"analyzingScene", "abandoned", "failed"},
    "analyzingScene": {"awaitingObjectReview", "abandoned", "failed"},
    "awaitingObjectReview": {"analyzingScene", "generatingTasks", "abandoned", "failed"},
    "generatingTasks": {"awaitingObjectReview", "ready", "inProgress", "abandoned", "failed"},
    "ready": {"inProgress", "abandoned", "failed"},
    "inProgress": {"completed", "abandoned", "failed"},
    "completed": set(),
    "abandoned": set(),
    "failed": set(),
}
READ_TASKS = {"vocabularyIntroduction", "grammarExplanation", "syntaxExplanation"}
ANALYSIS_TIMEOUT = timedelta(minutes=15)


def task_progress(tasks):
    complete = sum(t.status == "completed" for t in tasks)
    skipped = sum(t.status == "skipped" for t in tasks)
    return SessionProgress(
        completed_task_count=complete,
        skipped_task_count=skipped,
        terminal_task_count=complete + skipped,
        total_task_count=len(tasks),
    )


def parse_session(row):
    return Session.model_validate({k: row[k] for k in Session.model_fields})


PROCESSING_STATUSES = ("analyzingScene", "generatingTasks")
PROCESSING_FAILURE_CODES = {
    "analyzingScene": "sceneAnalysisFailed",
    "generatingTasks": "taskGenerationFailed",
}


def _stale_processing(status=None):
    """The one staleness predicate shared by the read check, `_active_row` and `_reap`."""
    return and_(
        sessions.c.status == status if status else sessions.c.status.in_(PROCESSING_STATUSES),
        sessions.c.analysis_draft["processingStartedAt"].astext.cast(DateTime(timezone=True))
        < utc_now() - ANALYSIS_TIMEOUT,
    )


class PostgresWorkflowRepository:
    def __init__(
        self,
        engine,
        user_id,
        analyzer=None,
        private_media_urls: PrivateMediaUrls | None = None,
        media_public_base_url: str | None = None,
    ):
        self.engine, self.user_id = engine, user_id
        self.analyzer = analyzer or DeterministicSceneAnalyzer(engine)
        self.private_media_urls = private_media_urls
        self.media_public_base_url = media_public_base_url

    @contextmanager
    def transaction(self):
        try:
            with self.engine.begin() as connection:
                if (
                    connection.execute(
                        select(users.c.id).where(users.c.id == self.user_id).with_for_update()
                    ).scalar_one_or_none()
                    is None
                ):
                    raise PracticeNotFoundError("User not found.")
                yield connection
        except SQLAlchemyError as exc:
            raise PracticeStorageError("Unable to save the session workflow.") from exc

    @contextmanager
    def read_connection(self):
        """Reads need a consistent snapshot, not the per-user write lock."""
        try:
            with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
                yield c
        except SQLAlchemyError as exc:
            raise PracticeStorageError("Unable to read the session workflow.") from exc

    def _session(self, c, session_id, profile_id=None):
        query = select(sessions).where(
            sessions.c.id == session_id, sessions.c.user_id == self.user_id
        )
        if profile_id:
            query = query.where(sessions.c.language_profile_id == profile_id)
        row = c.execute(query).mappings().one_or_none()
        if row is None:
            raise PracticeNotFoundError("Session not found.")
        return parse_session(row)

    def _transition(self, c, session, target, **extra):
        """Compare-and-set a session status; only listed edges are legal."""
        if session.status == target:
            return session
        if target not in ALLOWED_TRANSITIONS[session.status]:
            raise PracticeConflictError(
                f"Session cannot move from {session.status!r} to {target!r}."
            )
        values = dict(extra, status=target)
        if target in {"analyzingScene", "generatingTasks"}:
            # The session model has no updated_at; keep the processing clock in its draft.
            values["analysis_draft"] = {
                **(extra.get("analysis_draft", session.analysis_draft) or {}),
                "processingStartedAt": utc_now().isoformat(),
            }
        if target == "inProgress":
            values["started_at"] = session.started_at or utc_now()
        elif target == "completed":
            values["completed_at"] = utc_now()
        elif target == "abandoned":
            values["abandoned_at"] = utc_now()
        changed = c.execute(
            update(sessions)
            .where(sessions.c.id == session.id, sessions.c.status == session.status)
            .values(**values)
        ).rowcount
        if not changed:
            raise PracticeConflictError(
                "Session changed while this request was running. Retry the action."
            )
        return session.model_copy(update={**values, "status": SessionStatus(target)})

    def _tasks(self, c, session_id):
        return [
            SessionTask.model_validate(dict(r))
            for r in c.execute(
                select(session_tasks)
                .where(session_tasks.c.session_id == session_id)
                .order_by(session_tasks.c.order_index)
            ).mappings()
        ]

    def _image_url(self, asset):
        try:
            if self.private_media_urls is not None:
                return self.private_media_urls.resolve([asset.storage_key]).get(asset.storage_key)
            return public_media_url(asset.storage_key, self.media_public_base_url)
        except MediaUrlError:
            # A signing outage must not roll back the surrounding session transaction.
            return None

    def _detail(self, c, session):
        asset = MediaAsset.model_validate(
            dict(
                c.execute(
                    select(media_assets).where(media_assets.c.id == session.scene_media_asset_id)
                )
                .mappings()
                .one()
            )
        )
        scene = (
            c.execute(
                select(preloaded_scenes.c.slug, preloaded_scenes.c.title).where(
                    preloaded_scenes.c.media_asset_id == asset.id
                )
            )
            .mappings()
            .first()
            if asset.source == "preloaded"
            else None
        )
        draft = session.analysis_draft
        use_draft = bool(draft) and session.status in {
            "created",
            "analyzingScene",
            "awaitingObjectReview",
        }
        if use_draft:
            objects = [SceneObject.model_validate(obj) for obj in draft.get("objects", [])]
            relations = [
                SceneObjectRelation.model_validate(row) for row in draft.get("relations", [])
            ]
        else:
            objects = []
            relations = []
            seen_objects = set()
            for row in c.execute(
                select(
                    scene_objects,
                    *[column.label(f"r_{column.name}") for column in scene_object_relations.c],
                )
                .select_from(
                    scene_objects.outerjoin(
                        scene_object_relations,
                        scene_object_relations.c.subject_scene_object_id == scene_objects.c.id,
                    )
                )
                .where(scene_objects.c.session_id == session.id)
                .order_by(scene_objects.c.id)
            ).mappings():
                if row["id"] not in seen_objects:
                    seen_objects.add(row["id"])
                    objects.append(
                        SceneObject.model_validate({k: row[k] for k in SceneObject.model_fields})
                    )
                if row["r_id"] is not None:
                    relations.append(
                        SceneObjectRelation.model_validate(
                            {k: row[f"r_{k}"] for k in SceneObjectRelation.model_fields}
                        )
                    )
        ids = [o.vocabulary_item_id for o in objects if o.vocabulary_item_id]
        words = []
        translations = []
        if ids:
            source = (
                select(language_profiles.c.source_language_code)
                .where(language_profiles.c.id == session.language_profile_id)
                .scalar_subquery()
            )
            seen = set()
            for row in c.execute(
                select(
                    vocabulary_items,
                    *[column.label(f"t_{column.name}") for column in vocabulary_translations.c],
                )
                .select_from(
                    vocabulary_items.outerjoin(
                        vocabulary_translations,
                        and_(
                            vocabulary_translations.c.vocabulary_item_id == vocabulary_items.c.id,
                            func.lower(vocabulary_translations.c.source_language_code)
                            == func.lower(source),
                        ),
                    )
                )
                .where(vocabulary_items.c.id.in_(ids))
            ).mappings():
                if row["id"] not in seen:
                    seen.add(row["id"])
                    words.append(
                        VocabularyItem.model_validate(
                            {k: row[k] for k in VocabularyItem.model_fields}
                        )
                    )
                if row["t_id"] is not None:
                    translations.append(
                        VocabularyTranslation.model_validate(
                            {k: row[f"t_{k}"] for k in VocabularyTranslation.model_fields}
                        )
                    )
        tasks = self._tasks(c, session.id)
        return SessionDetailResponse(
            session=session,
            media_asset=asset,
            image_url=self._image_url(asset),
            scene_id=scene["slug"] if scene else None,
            title=session.session_title or (scene["title"] if scene else "Your uploaded photo"),
            analysis_mode=None if asset.source == "preloaded" else "placeholder",
            scene_objects=objects,
            scene_object_relations=relations,
            vocabulary=words,
            translations=translations,
            tasks=[SessionTaskPublic.from_internal(t) for t in tasks],
            progress=task_progress(tasks),
            next_task_id=next(
                (t.id for t in tasks if t.status not in {"completed", "skipped"}), None
            ),
        )

    def _active_row(self, c, profile_id):
        return (
            c.execute(
                select(
                    sessions,
                    _stale_processing().label("is_stale"),
                )
                .where(
                    sessions.c.user_id == self.user_id,
                    sessions.c.language_profile_id == profile_id,
                    sessions.c.status.not_in(TERMINAL),
                )
                .order_by(sessions.c.started_at.desc().nulls_last(), sessions.c.id)
            )
            .mappings()
            .first()
        )

    def get(self, session_id, profile_id=None):
        with self.read_connection() as c:
            session = self._session(c, session_id, profile_id)
            if session.status not in PROCESSING_STATUSES:
                return self._detail(c, session)
            stale = c.execute(
                select(_stale_processing()).select_from(sessions).where(sessions.c.id == session.id)
            ).scalar_one()
            if not stale:
                return self._detail(c, session)
        # Only an expired processing session needs the write path.
        with self.transaction() as c:
            self._expire_stale(
                c,
                sessions.c.id == session_id,
                sessions.c.user_id == self.user_id,
            )
            return self._detail(c, self._session(c, session_id, profile_id))

    def status(self, session_id, profile_id=None):
        with self.read_connection() as c:
            session = self._session(c, session_id, profile_id)
            response = SessionStatusResponse(
                id=session.id, status=session.status, failure_code=session.failure_code
            )
            if session.status not in PROCESSING_STATUSES:
                return response
            stale = c.execute(
                select(_stale_processing())
                .select_from(sessions)
                .where(sessions.c.id == session.id)
            ).scalar_one()
            if not stale:
                return response
        with self.transaction() as c:
            self._expire_stale(
                c,
                sessions.c.id == session_id,
                sessions.c.user_id == self.user_id,
            )
            session = self._session(c, session_id, profile_id)
            return SessionStatusResponse(
                id=session.id, status=session.status, failure_code=session.failure_code
            )

    def active(self, profile_id):
        try:
            with self.read_connection() as c:
                if (
                    c.execute(
                        select(users.c.id).where(users.c.id == self.user_id)
                    ).scalar_one_or_none()
                    is None
                ):
                    return None
                row = self._active_row(c, profile_id)
                if row is None:
                    return None
                if not row["is_stale"]:
                    return self._detail(c, parse_session(row))
            # Only an expired processing session needs the write path.
            with self.transaction() as c:
                self._reap(c, profile_id)
                row = self._active_row(c, profile_id)
                return self._detail(c, parse_session(row)) if row else None
        except PracticeNotFoundError:
            return None

    def create(self, request):
        with self.transaction() as c:
            profile = (
                c.execute(
                    select(language_profiles).where(
                        language_profiles.c.id == request.language_profile_id,
                        language_profiles.c.user_id == self.user_id,
                        language_profiles.c.is_active.is_(True),
                    )
                )
                .mappings()
                .one_or_none()
            )
            if profile is None:
                raise PracticeConflictError("Select the active language profile.")
            asset = (
                c.execute(select(media_assets).where(media_assets.c.id == request.media_asset_id))
                .mappings()
                .one_or_none()
            )
            if (
                not asset
                or asset["media_type"] != "image"
                or not (
                    (asset["source"] == "preloaded" and asset["owner_user_id"] is None)
                    or (
                        asset["source"] in {"camera", "userUpload"}
                        and asset["owner_user_id"] == self.user_id
                    )
                )
            ):
                raise PracticeNotFoundError("Image not found.")
            if (
                asset["source"] == "preloaded"
                and c.execute(
                    select(preloaded_scenes.c.id).where(
                        preloaded_scenes.c.media_asset_id == asset["id"],
                        preloaded_scenes.c.is_active.is_(True),
                        func.lower(preloaded_scenes.c.language_code)
                        == profile["target_language_code"].lower(),
                    )
                ).first()
                is None
            ):
                raise PracticeNotFoundError("Scene not found for this language.")
            if request.idempotency_key:
                existing = (
                    c.execute(
                        select(sessions).where(
                            sessions.c.user_id == self.user_id,
                            sessions.c.language_profile_id == request.language_profile_id,
                            sessions.c.idempotency_key == request.idempotency_key,
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if existing:
                    if existing["scene_media_asset_id"] != request.media_asset_id:
                        raise PracticeConflictError("This request key was used for another image.")
                    return self._detail(c, parse_session(existing))
            self._reap(c, request.language_profile_id)
            existing = (
                c.execute(
                    select(sessions).where(
                        sessions.c.user_id == self.user_id,
                        sessions.c.language_profile_id == request.language_profile_id,
                        sessions.c.status.not_in(TERMINAL),
                    )
                )
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                if existing["scene_media_asset_id"] == request.media_asset_id:
                    return self._detail(c, parse_session(existing))
                raise ActiveSessionExistsError(
                    "You have a practice session in progress. "
                    "Continue it or discard it before starting a new one.",
                    active_session_id=existing["id"],
                )
            session = Session(
                user_id=self.user_id,
                language_profile_id=request.language_profile_id,
                scene_media_asset_id=request.media_asset_id,
                idempotency_key=request.idempotency_key,
            )
            c.execute(insert(sessions).values(**session.model_dump(by_alias=False)))
            return self._detail(c, session)

    def _expire_stale(self, c, *scope):
        """Fail stale processing sessions inside `scope` with their status's code."""
        for status, failure_code in PROCESSING_FAILURE_CODES.items():
            c.execute(
                update(sessions)
                .where(*scope, _stale_processing(status))
                .values(status="failed", failure_code=failure_code)
            )

    def _reap(self, c, profile_id):
        """Expire stale non-terminal sessions so a crashed request cannot block a new run."""
        self._expire_stale(
            c,
            sessions.c.user_id == self.user_id,
            sessions.c.language_profile_id == profile_id,
        )

    def analyze(self, session_id, profile_id):
        with self.transaction() as c:
            session = self._session(c, session_id, profile_id)
            if session.status in TERMINAL:
                raise PracticeConflictError("Cannot analyze a terminal session.")
            if session.status in {"ready", "inProgress"}:
                raise PracticeConflictError("Session analysis is already finished.")
            if session.status != "created":
                # analyzingScene/awaitingObjectReview/generatingTasks: never re-run the model.
                return self._detail(c, session)
            asset = MediaAsset.model_validate(
                dict(
                    c.execute(
                        select(media_assets).where(
                            media_assets.c.id == session.scene_media_asset_id
                        )
                    )
                    .mappings()
                    .one()
                )
            )
            profile = (
                c.execute(
                    select(language_profiles).where(
                        language_profiles.c.id == session.language_profile_id
                    )
                )
                .mappings()
                .one()
            )
            scene = (
                c.execute(
                    select(preloaded_scenes).where(preloaded_scenes.c.media_asset_id == asset.id)
                )
                .mappings()
                .first()
                if asset.source == "preloaded"
                else None
            )
            if asset.source == "preloaded" and scene is None:
                raise PracticeNotFoundError("Curated scene not found.")
            claimed = self._transition(c, session, "analyzingScene")
        try:
            result = self.analyzer.analyze(
                claimed, asset, dict(profile), dict(scene) if scene else None
            )
        except Exception as exc:
            with self.transaction() as c:
                current = self._session(c, session_id)
                if current.status == "analyzingScene":
                    self._transition(c, current, "failed", failure_code="sceneAnalysisFailed")
            if isinstance(exc, PracticeConflictError | PracticeNotFoundError):
                raise
            raise SceneAnalysisError("Scene analysis failed.") from exc
        with self.transaction() as c:
            current = self._session(c, session_id, profile_id)
            if current.status != "analyzingScene":
                return self._detail(c, current)
            current = self._transition(
                c,
                current,
                "awaitingObjectReview",
                session_title=result.title,
                session_summary=result.summary,
                analysis_draft={
                    "objects": [
                        obj.model_dump(mode="json", by_alias=False) for obj in result.objects
                    ],
                    "relations": [
                        row.model_dump(mode="json", by_alias=False) for row in result.relations
                    ],
                },
            )
            return self._detail(c, current)

    def _catalog_word(self, c, profile, label):
        match = (
            c.execute(
                select(vocabulary_items, vocabulary_translations.c.translated_text)
                .join(
                    vocabulary_translations,
                    vocabulary_translations.c.vocabulary_item_id == vocabulary_items.c.id,
                )
                .where(
                    func.lower(vocabulary_items.c.language_code)
                    == profile["target_language_code"].lower(),
                    func.lower(vocabulary_translations.c.source_language_code)
                    == profile["source_language_code"].lower(),
                    func.lower(vocabulary_translations.c.translated_text) == label.strip().lower(),
                )
                .order_by(vocabulary_items.c.id)
                .limit(1)
            )
            .mappings()
            .first()
        )
        if not match:
            raise PracticeConflictError(
                f'"{label}" is not in the vocabulary for your learning language yet. '
                "Please choose another word."
            )
        return VocabularyItem.model_validate(
            {key: match[key] for key in VocabularyItem.model_fields}
        )

    def check_word(self, session_id, profile_id, label):
        with self.engine.connect() as c:
            self._session(c, session_id, profile_id)
            profile = (
                c.execute(select(language_profiles).where(language_profiles.c.id == profile_id))
                .mappings()
                .one()
            )
            self._catalog_word(c, profile, label)
            return {"available": True}

    def review(self, session_id, profile_id, request):
        with self.transaction() as c:
            session = self._session(c, session_id, profile_id)
            if session.status in TERMINAL:
                raise PracticeConflictError("This session cannot be edited.")
            tasks = self._tasks(c, session_id)
            if (
                any(task.status != "pending" for task in tasks)
                or c.execute(
                    select(task_attempts.c.id)
                    .join(session_tasks, session_tasks.c.id == task_attempts.c.session_task_id)
                    .where(session_tasks.c.session_id == session_id)
                    .limit(1)
                ).first()
            ):
                raise PracticeConflictError(
                    "Practice has started. Start a new session to change its words."
                )
            detail = self._detail(c, session)
            existing = {obj.id: obj for obj in detail.scene_objects}
            if any(object_id not in existing for object_id in request.accepted_object_ids):
                raise PracticeConflictError("An object does not belong to this session.")
            profile = (
                c.execute(select(language_profiles).where(language_profiles.c.id == profile_id))
                .mappings()
                .one()
            )
            for object_id in request.accepted_object_ids:
                obj = existing[object_id]
                c.execute(
                    upsert(scene_objects)
                    .values(**object_values(obj))
                    .on_conflict_do_nothing(index_elements=["id"])
                )
            for added in request.added_objects:
                # Scope client-generated IDs to this session; retries keep the same object.
                object_id = uuid5(session_id, "manual:" + str(added.id))
                word = self._catalog_word(c, profile, added.label)
                obj = SceneObject(
                    id=object_id,
                    session_id=session_id,
                    label=added.label,
                    vocabulary_item_id=word.id,
                    bounding_box={"x": added.x, "y": added.y, "width": 0.01, "height": 0.01},
                )
                values = object_values(obj)
                c.execute(
                    upsert(scene_objects)
                    .values(**values)
                    .on_conflict_do_update(
                        index_elements=["id"],
                        set_={key: value for key, value in values.items() if key != "id"},
                    )
                )
            accepted = set(request.accepted_object_ids) | {
                uuid5(session_id, "manual:" + str(added.id)) for added in request.added_objects
            }
            c.execute(delete(session_tasks).where(session_tasks.c.session_id == session_id))
            c.execute(
                delete(scene_objects).where(
                    scene_objects.c.session_id == session_id, scene_objects.c.id.not_in(accepted)
                )
            )
            c.execute(
                delete(scene_object_relations).where(
                    scene_object_relations.c.subject_scene_object_id.in_(
                        select(scene_objects.c.id).where(scene_objects.c.session_id == session_id)
                    )
                )
            )
            manual_ids = {
                item.id: uuid5(session_id, "manual:" + str(item.id))
                for item in request.added_objects
            }
            original_relations = {row.id: row for row in detail.scene_object_relations}
            for relation in request.relations:
                original = original_relations.get(relation.id)
                # Provenance is preserved only for unchanged server-generated suggestions.
                source_key = (
                    original.source_relation_key
                    if original
                    and (
                        original.subject_scene_object_id == relation.subject_scene_object_id
                        and original.reference_scene_object_id == relation.reference_scene_object_id
                        and original.relation == relation.relation
                    )
                    else None
                )
                c.execute(
                    insert(scene_object_relations).values(
                        id=relation.id
                        if original
                        else uuid5(session_id, "relation:" + str(relation.id)),
                        subject_scene_object_id=manual_ids.get(
                            relation.subject_scene_object_id, relation.subject_scene_object_id
                        ),
                        reference_scene_object_id=manual_ids.get(
                            relation.reference_scene_object_id, relation.reference_scene_object_id
                        ),
                        relation=relation.relation,
                        source_relation_key=source_key,
                    )
                )
            if session.status not in {"ready", "inProgress"}:
                session = self._transition(c, session, "generatingTasks")
            detail = self._detail(c, session)
            objects = [obj for obj in detail.scene_objects if obj.id in accepted]
            words_by_id = {word.id: word for word in detail.vocabulary}
            translations_by_id = {word.vocabulary_item_id: word for word in detail.translations}
            if any(
                obj.vocabulary_item_id not in words_by_id
                or obj.vocabulary_item_id not in translations_by_id
                for obj in objects
            ):
                raise PracticeConflictError("Every selected object needs a word and translation.")
            words = [words_by_id[obj.vocabulary_item_id] for obj in objects]
            translations = [translations_by_id[obj.vocabulary_item_id] for obj in objects]
            rebuilt = build_tasks(session_id, objects, words, translations, False)
            # Every kept object gets vocabulary and pronunciation practice, not just the first.
            extra = []
            for obj, word, translation in zip(
                objects[1:], words[1:], translations[1:], strict=True
            ):
                for task in build_tasks(session_id, [obj], [word], [translation], False)[:2]:
                    task.id = uuid5(obj.id, "review:" + task.kind.value)
                    extra.append(task)
            rebuilt = rebuilt[:2] + extra + rebuilt[2:]
            for index, task in enumerate(rebuilt):
                task.order_index = index
                c.execute(insert(session_tasks).values(**entity_values(task)))
            session = self._transition(c, session, "inProgress")
            return self._detail(c, session)

    def finish(self, session_id, profile_id, abandon=False):
        with self.transaction() as c:
            session = self._session(c, session_id, profile_id)
            target = "abandoned" if abandon else "completed"
            if session.status == target:
                return session
            if session.status in TERMINAL:
                raise PracticeConflictError("Session is already terminal.")
            tasks = self._tasks(c, session.id)
            if not abandon and (
                not tasks or any(t.status not in {"completed", "skipped"} for t in tasks)
            ):
                raise PracticeConflictError("Complete or skip every task first.")
            return self._transition(c, session, target)

    def summary(self, session_id, profile_id):
        with self.read_connection() as c:
            session = self._session(c, session_id, profile_id)
            learned = (
                c.execute(
                    select(vocabulary_encounters.c.vocabulary_item_id)
                    .where(
                        vocabulary_encounters.c.session_id == session.id,
                        vocabulary_encounters.c.user_id == self.user_id,
                    )
                    .distinct()
                )
                .scalars()
                .all()
            )
            return SessionSummaryResponse(
                session=session,
                progress=task_progress(self._tasks(c, session.id)),
                learned_vocabulary_ids=learned,
                xp_earned=c.execute(
                    select(func.count())
                    .select_from(vocabulary_encounters)
                    .where(
                        vocabulary_encounters.c.session_id == session.id,
                        vocabulary_encounters.c.user_id == self.user_id,
                    )
                ).scalar_one()
                * 5,
                **self._ispy_summary(c, session.id),
            )

    def _ispy_summary(self, c, session_id):
        outcomes = (
            c.execute(
                select(task_attempts.c.is_correct)
                .join(session_tasks, session_tasks.c.id == task_attempts.c.session_task_id)
                .where(
                    session_tasks.c.session_id == session_id, session_tasks.c.kind == "ispyRound"
                )
            )
            .scalars()
            .all()
        )
        return {
            "ispy_correct_count": sum(outcome is True for outcome in outcomes),
            "ispy_attempt_count": sum(outcome is not None for outcome in outcomes),
        }

    def _encounter(self, c, task, event_id, outcome, introduced=False):
        if not task.vocabulary_item_id:
            return
        initial = UserVocabularyProgress(
            user_id=self.user_id, vocabulary_item_id=task.vocabulary_item_id
        )
        c.execute(
            upsert(user_vocabulary_progress)
            .values(**initial.model_dump(by_alias=False))
            .on_conflict_do_nothing(index_elements=["user_id", "vocabulary_item_id"])
        )
        event = VocabularyEncounter(
            id=uuid5(event_id, "vocabulary"),
            user_id=self.user_id,
            vocabulary_item_id=task.vocabulary_item_id,
            session_id=task.session_id,
            session_task_id=task.id,
            encounter_type="introduced" if introduced else "practised",
            outcome=outcome,
        )
        saved = c.execute(
            upsert(vocabulary_encounters)
            .values(**event.model_dump(by_alias=False))
            .on_conflict_do_nothing(index_elements=["id"])
            .returning(vocabulary_encounters.c.id)
        ).scalar_one_or_none()
        if saved:
            values = dict(
                status=case(
                    (user_vocabulary_progress.c.status == "new", "learning"),
                    else_=user_vocabulary_progress.c.status,
                ),
                exposure_count=user_vocabulary_progress.c.exposure_count + 1,
                correct_attempt_count=user_vocabulary_progress.c.correct_attempt_count
                + int(outcome == "correct"),
                first_learned_at=func.coalesce(
                    user_vocabulary_progress.c.first_learned_at, event.occurred_at
                ),
            )
            if not introduced:
                values["last_practised_at"] = event.occurred_at
            c.execute(
                update(user_vocabulary_progress)
                .where(
                    user_vocabulary_progress.c.user_id == self.user_id,
                    user_vocabulary_progress.c.vocabulary_item_id == task.vocabulary_item_id,
                )
                .values(**values)
            )

    def task_action(self, task_id, action, request=None):
        with self.transaction() as c:
            row = (
                c.execute(
                    select(session_tasks)
                    .join(sessions, sessions.c.id == session_tasks.c.session_id)
                    .join(
                        language_profiles, language_profiles.c.id == sessions.c.language_profile_id
                    )
                    .where(
                        session_tasks.c.id == task_id,
                        sessions.c.user_id == self.user_id,
                        language_profiles.c.is_active.is_(True),
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise PracticeNotFoundError("Task not found.")
            task = SessionTask.model_validate(dict(row))
            session = self._session(c, task.session_id)
            attempt = None
            if action == "attempt":
                payload = request.model_dump(
                    mode="json", by_alias=False, exclude={"idempotency_key"}
                )
                attempt_id = uuid5(
                    task.id, "attempt:" + (request.idempotency_key or "single-evaluation")
                )
                saved = (
                    c.execute(select(task_attempts).where(task_attempts.c.id == attempt_id))
                    .mappings()
                    .one_or_none()
                )
                if saved:
                    attempt = TaskAttempt.model_validate(dict(saved))
                    if attempt.response_payload != payload:
                        raise PracticeConflictError("Attempt key already used for another answer.")
            retry = (
                attempt is not None
                or (action == "complete" and task.status == "completed")
                or (action == "skip" and task.status == "skipped")
            )
            if not retry:
                if session.status != "inProgress" or task.status in {"completed", "skipped"}:
                    raise PracticeConflictError(
                        f"Task or session is not active; session is '{session.status}'."
                    )
                values = {}
                if action == "start":
                    values = dict(status="inProgress", started_at=task.started_at or utc_now())
                elif action == "skip":
                    values = dict(
                        status="skipped", skipped_at=utc_now(), skip_reason=request.reason
                    )
                elif action == "complete":
                    if task.kind not in READ_TASKS:
                        raise PracticeConflictError("Submit an answer or skip this task.")
                    values = dict(
                        status="completed",
                        completed_at=utc_now(),
                        started_at=task.started_at or utc_now(),
                    )
                    if task.kind == "vocabularyIntroduction":
                        self._encounter(c, task, task.id, "completed", introduced=True)
                elif action == "attempt":
                    correct = evaluate(task, request)
                    attempt = TaskAttempt(
                        id=attempt_id,
                        session_task_id=task.id,
                        attempt_number=1,
                        input_mode=request.input_mode,
                        response_payload=payload,
                        is_correct=correct,
                        score=None if correct is None else int(correct),
                        feedback={
                            "message": "Reflection recorded."
                            if correct is None
                            else (
                                "Correct."
                                if correct
                                else "Not quite. Review this word and try it in another session."
                            )
                        },
                    )
                    c.execute(insert(task_attempts).values(**entity_values(attempt)))
                    self._encounter(
                        c,
                        task,
                        attempt.id,
                        "completed" if correct is None else ("correct" if correct else "incorrect"),
                    )
                    values = dict(
                        status="completed",
                        completed_at=utc_now(),
                        started_at=task.started_at or utc_now(),
                    )
                else:
                    raise PracticeConflictError("Unknown task action.")
                c.execute(
                    update(session_tasks).where(session_tasks.c.id == task.id).values(**values)
                )
            tasks = self._tasks(c, task.session_id)
            return TaskActionResponse(
                task=SessionTaskPublic.from_internal(next(t for t in tasks if t.id == task.id)),
                attempt=attempt,
                next_task_id=next(
                    (t.id for t in tasks if t.status not in {"completed", "skipped"}), None
                ),
                session_progress=task_progress(tasks),
            )


def evaluate(task, request):
    """Small deterministic evaluator; never accepts client scores or answer keys."""
    mode = request.input_mode
    if task.kind in READ_TASKS:
        raise PracticeConflictError("This task is completed by reading it.")
    allowed = {
        "pronunciationPractice": {"text"},
        "grammarPractice": {"text", "multipleChoice"},
        "sentenceBuilding": {"text"},
        "ispyRound": {"objectSelection", "multipleChoice"},
        "reflection": {"text"},
    }
    if mode not in allowed.get(task.kind, set()):
        raise PracticeConflictError(
            "Input mode is not supported for this task. Use typing or the offered choices."
        )
    if task.kind == "reflection":
        return None
    key = task.answer_key
    if key is None:
        raise PracticeConflictError("Task has no evaluation key.")
    if mode == "objectSelection":
        if request.scene_object_id not in {o.scene_object_id for o in task.public_content.options}:
            raise PracticeConflictError("Select an object offered by this task.")
        return request.scene_object_id == key.correct_scene_object_id
    if mode == "multipleChoice":
        options = task.public_content.options
        offered = {o.option_id for o in options} if task.kind == "ispyRound" else set(options)
        if request.option_id not in offered:
            raise PracticeConflictError("Select one of the offered choices.")
        return request.option_id == key.correct_option_id

    def normalize(value):
        return " ".join(value.casefold().strip().split()).rstrip(".!?\u3002")  # noqa: B005

    return normalize(request.text) in {normalize(a) for a in key.accepted_text_answers}
