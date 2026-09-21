"""PostgreSQL vocabulary persistence."""

from datetime import datetime
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import (
    Column,
    DateTime,
    Engine,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Uuid,
    func,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.learning import LearningStorageError
from app.repositories.postgres.language_profiles import language_profiles
from app.repositories.postgres.practice import sessions
from app.repositories.postgres.scenes import preloaded_scenes
from app.repositories.postgres.users import users
from app.repositories.postgres.xp import award
from app.schemas.base import utc_now
from app.schemas.vocabulary import (
    DailyVocabularyItem,
    UserVocabularyProgress,
    VocabularyEncounter,
    VocabularyItem,
    VocabularyTranslation,
)
from app.services.vocabulary_mastery import Evidence, derive_progress

metadata = MetaData()


def entity_columns():
    return [
        Column("id", Uuid, primary_key=True),
        Column("created_at", DateTime(timezone=True), nullable=False),
        Column("updated_at", DateTime(timezone=True), nullable=False),
    ]


vocabulary_items = Table(
    "vocabulary_items",
    metadata,
    *entity_columns(),
    Column("language_code", String(35), nullable=False),
    Column("lemma", String(200), nullable=False),
    Column("display_text", String(200), nullable=False),
    Column("part_of_speech", String(13), nullable=False),
    Column("gender", String(50)),
    Column("plural_form", String(200)),
    Column("phonetic_text", String(300)),
    Column("pronunciation_audio_asset_id", Uuid),
    Column("example_sentence", String(1000)),
    Column("difficulty_level", String(2)),
    schema="public",
)
vocabulary_translations = Table(
    "vocabulary_translations",
    metadata,
    *entity_columns(),
    Column("vocabulary_item_id", Uuid, nullable=False),
    Column("source_language_code", String(35), nullable=False),
    Column("translated_text", String(300), nullable=False),
    Column("short_definition", String(1000)),
    schema="public",
)
user_vocabulary_progress = Table(
    "user_vocabulary_progress",
    metadata,
    *entity_columns(),
    Column("user_id", Uuid, nullable=False),
    Column("vocabulary_item_id", Uuid, nullable=False),
    Column("status", String(8), nullable=False),
    Column("exposure_count", Integer, nullable=False),
    Column("correct_attempt_count", Integer, nullable=False),
    Column("mastery_score", Numeric(6, 5), nullable=False),
    Column("first_learned_at", DateTime(timezone=True)),
    Column("last_practised_at", DateTime(timezone=True)),
    schema="public",
)
vocabulary_encounters = Table(
    "vocabulary_encounters",
    metadata,
    *entity_columns(),
    Column("user_id", Uuid, nullable=False),
    Column("vocabulary_item_id", Uuid, nullable=False),
    Column("session_id", Uuid, nullable=False),
    Column("session_task_id", Uuid, nullable=False),
    Column("encounter_type", String(10), nullable=False),
    Column("outcome", String(9), nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    schema="public",
)


class VocabularyEncounterConflictError(Exception):
    """An existing event ID was reused with different event data."""


def record_vocabulary_evidence(
    connection,
    *,
    user_id: UUID,
    vocabulary_item_id: UUID,
    encounter: VocabularyEncounter | None = None,
    usage_at: datetime | None = None,
    language_profile_id: UUID | None = None,
    session_id: UUID | None = None,
    now: datetime | None = None,
) -> VocabularyEncounter | None:
    """Single write path for learning evidence; status is rederived from all of it."""
    initial = UserVocabularyProgress(user_id=user_id, vocabulary_item_id=vocabulary_item_id)
    connection.execute(
        insert(user_vocabulary_progress)
        .values(**initial.model_dump(by_alias=False))
        .on_conflict_do_nothing(index_elements=["user_id", "vocabulary_item_id"])
    )
    # Locking the progress row serializes concurrent writers for this word.
    stored = (
        connection.execute(
            select(user_vocabulary_progress)
            .where(
                user_vocabulary_progress.c.user_id == user_id,
                user_vocabulary_progress.c.vocabulary_item_id == vocabulary_item_id,
            )
            .with_for_update()
        )
        .mappings()
        .one()
    )
    if encounter is not None:
        inserted = connection.execute(
            insert(vocabulary_encounters)
            .values(**encounter.model_dump(by_alias=False))
            .on_conflict_do_nothing(index_elements=["id"])
            .returning(vocabulary_encounters.c.id)
        ).scalar_one_or_none()
        if inserted is None:
            existing = VocabularyEncounter.model_validate(
                dict(
                    connection.execute(
                        select(vocabulary_encounters).where(
                            vocabulary_encounters.c.id == encounter.id
                        )
                    )
                    .mappings()
                    .one()
                )
            )
            excluded = {"created_at", "updated_at"}
            if existing.model_dump(exclude=excluded) != encounter.model_dump(exclude=excluded):
                raise VocabularyEncounterConflictError("Encounter ID already has different data.")
            return existing
    evidence = [
        Evidence(
            occurred_at=row["occurred_at"],
            encounter_type=row["encounter_type"],
            outcome=row["outcome"],
        )
        for row in connection.execute(
            select(
                vocabulary_encounters.c.occurred_at,
                vocabulary_encounters.c.encounter_type,
                vocabulary_encounters.c.outcome,
            ).where(
                vocabulary_encounters.c.user_id == user_id,
                vocabulary_encounters.c.vocabulary_item_id == vocabulary_item_id,
            )
        ).mappings()
    ]
    timezone = connection.execute(
        select(users.c.timezone).where(users.c.id == user_id)
    ).scalar_one()
    derived = derive_progress(evidence, timezone=timezone, now=now or utc_now())
    # Usage without an encounter (journal writes) refreshes recency but never
    # moves last_practised_at backwards.
    last_practised = max(
        (
            moment
            for moment in (
                stored["last_practised_at"], derived.last_practised_at, usage_at
            )
            if moment is not None
        ),
        default=None,
    )
    connection.execute(
        update(user_vocabulary_progress)
        .where(
            user_vocabulary_progress.c.user_id == user_id,
            user_vocabulary_progress.c.vocabulary_item_id == vocabulary_item_id,
        )
        .values(
            status=derived.status,
            mastery_score=derived.mastery_score,
            exposure_count=derived.exposure_count,
            correct_attempt_count=derived.correct_attempt_count,
            first_learned_at=derived.first_learned_at,
            last_practised_at=last_practised,
            updated_at=utc_now(),
        )
    )
    if stored["status"] != "mastered" and derived.status == "mastered":
        award(
            connection,
            user_id=user_id,
            event_type="vocabularyMastered",
            idempotency_key=f"mastery:{vocabulary_item_id}",
            language_profile_id=language_profile_id,
            session_id=session_id,
        )
    return encounter


class PostgresVocabularyRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def list_vocabulary(self, user_id: UUID) -> list[DailyVocabularyItem]:
        try:
            # One snapshot keeps translations/history consistent with the selected profile.
            with self.engine.connect().execution_options(
                isolation_level="REPEATABLE READ"
            ) as connection:
                profile = (
                    connection.execute(
                        select(language_profiles).where(
                            language_profiles.c.user_id == user_id,
                            language_profiles.c.is_active.is_(True),
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if profile is None:
                    return []
                rows = (
                    connection.execute(
                        select(user_vocabulary_progress)
                        .join(
                            vocabulary_items,
                            vocabulary_items.c.id == user_vocabulary_progress.c.vocabulary_item_id,
                        )
                        .where(
                            user_vocabulary_progress.c.user_id == user_id,
                            func.lower(vocabulary_items.c.language_code)
                            == profile["target_language_code"].lower(),
                        )
                        .order_by(
                            user_vocabulary_progress.c.created_at, user_vocabulary_progress.c.id
                        )
                    )
                    .mappings()
                    .all()
                )
                ids = [row["vocabulary_item_id"] for row in rows]
                if not ids:
                    return []
                items = {
                    row["id"]: VocabularyItem.model_validate(dict(row))
                    for row in connection.execute(
                        select(vocabulary_items).where(vocabulary_items.c.id.in_(ids))
                    ).mappings()
                }
                translations = {
                    row["vocabulary_item_id"]: VocabularyTranslation.model_validate(dict(row))
                    for row in connection.execute(
                        select(vocabulary_translations).where(
                            vocabulary_translations.c.vocabulary_item_id.in_(ids),
                            func.lower(vocabulary_translations.c.source_language_code)
                            == profile["source_language_code"].lower(),
                        )
                    ).mappings()
                }
                encounters: dict[UUID, list[UUID]] = {}
                histories: dict[UUID, list[Evidence]] = {}
                latest_session: dict[UUID, UUID] = {}
                for row in connection.execute(
                    select(vocabulary_encounters)
                    .where(
                        vocabulary_encounters.c.user_id == user_id,
                        vocabulary_encounters.c.vocabulary_item_id.in_(ids),
                    )
                    .order_by(vocabulary_encounters.c.occurred_at, vocabulary_encounters.c.id)
                ).mappings():
                    encounters.setdefault(row["vocabulary_item_id"], []).append(row["id"])
                    histories.setdefault(row["vocabulary_item_id"], []).append(
                        Evidence(
                            occurred_at=row["occurred_at"],
                            encounter_type=row["encounter_type"],
                            outcome=row["outcome"],
                        )
                    )
                    latest_session[row["vocabulary_item_id"]] = row["session_id"]
                # Status is derived, never trusted from the stored column, so
                # decayed words show their demoted rank without a write.
                timezone = connection.execute(
                    select(users.c.timezone).where(users.c.id == user_id)
                ).scalar_one()
                now = utc_now()
                # scene_id/topic describe the word's most recent encounter scene.
                scene_assets = (
                    {
                        row["id"]: row["scene_media_asset_id"]
                        for row in connection.execute(
                            select(sessions.c.id, sessions.c.scene_media_asset_id).where(
                                sessions.c.id.in_(set(latest_session.values()))
                            )
                        ).mappings()
                    }
                    if latest_session
                    else {}
                )
                scene_rows = (
                    {
                        row["media_asset_id"]: row
                        for row in connection.execute(
                            select(
                                preloaded_scenes.c.media_asset_id,
                                preloaded_scenes.c.slug,
                                preloaded_scenes.c.title,
                            ).where(preloaded_scenes.c.media_asset_id.in_(scene_assets.values()))
                        ).mappings()
                    }
                    if scene_assets
                    else {}
                )

                def scene(row):
                    scene_row = scene_rows.get(
                        scene_assets.get(latest_session.get(row["vocabulary_item_id"]))
                    )
                    return scene_row

                def progress(row):
                    derived = derive_progress(
                        histories.get(row["vocabulary_item_id"], []),
                        timezone=timezone,
                        now=now,
                    )
                    return UserVocabularyProgress.model_validate(
                        {key: row[key] for key in UserVocabularyProgress.model_fields}
                        | {"status": derived.status, "mastery_score": derived.mastery_score}
                    )

                return [
                    DailyVocabularyItem(
                        vocabulary=items[row["vocabulary_item_id"]],
                        translation=translations.get(row["vocabulary_item_id"]),
                        progress=progress(row),
                        scene_id=(scene(row) or {}).get("slug"),
                        topic=(scene(row) or {}).get("title"),
                        encounter_ids=encounters.get(row["vocabulary_item_id"], []),
                    )
                    for row in rows
                ]
        except (SQLAlchemyError, ValidationError) as exc:
            raise LearningStorageError("Unable to load vocabulary.") from exc

    def record_encounter(self, encounter: VocabularyEncounter) -> VocabularyEncounter:
        """Trusted evaluated events only. A stable event ID makes retries idempotent."""
        try:
            with self.engine.begin() as connection:
                owner = connection.execute(
                    select(users.c.id).where(users.c.id == encounter.user_id).with_for_update()
                ).scalar_one_or_none()
                if owner is None:
                    raise LearningStorageError("Encounter user does not exist.")
                return record_vocabulary_evidence(
                    connection,
                    user_id=encounter.user_id,
                    vocabulary_item_id=encounter.vocabulary_item_id,
                    encounter=encounter,
                )
        except (SQLAlchemyError, ValidationError) as exc:
            raise LearningStorageError("Unable to record vocabulary encounter.") from exc

    def record_journal_usage(
        self,
        *,
        user_id: UUID,
        language_profile_id: UUID,
        journal_id: UUID,
        words: list[str],
        occurred_at: datetime,
    ) -> list[UUID]:
        """Using a word in a journal is mastery evidence; unresolved text is ignored."""
        try:
            with self.engine.begin() as connection:
                profile = (
                    connection.execute(
                        select(language_profiles).where(
                            language_profiles.c.id == language_profile_id,
                            language_profiles.c.user_id == user_id,
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if profile is None:
                    return []
                labels = {word.strip().lower() for word in words}
                resolved = (
                    [
                        row["id"]
                        for row in connection.execute(
                            select(vocabulary_items.c.id)
                            .join(
                                user_vocabulary_progress,
                                user_vocabulary_progress.c.vocabulary_item_id
                                == vocabulary_items.c.id,
                            )
                            .where(
                                user_vocabulary_progress.c.user_id == user_id,
                                func.lower(vocabulary_items.c.display_text).in_(labels),
                                func.lower(vocabulary_items.c.language_code)
                                == profile["target_language_code"].lower(),
                            )
                            .distinct()
                        ).mappings()
                    ]
                    if labels
                    else []
                )
                for item_id in resolved:
                    # Journal usage is unevaluated evidence: it refreshes recency
                    # through usage_at but never promotes a word's status.
                    record_vocabulary_evidence(
                        connection,
                        user_id=user_id,
                        vocabulary_item_id=item_id,
                        usage_at=occurred_at,
                        language_profile_id=language_profile_id,
                    )
                award(
                    connection,
                    user_id=user_id,
                    event_type="journalEntry",
                    idempotency_key=f"journal:{journal_id}",
                    language_profile_id=language_profile_id,
                    occurred_at=occurred_at,
                )
                return resolved
        except (SQLAlchemyError, ValidationError) as exc:
            raise LearningStorageError("Unable to record journal vocabulary usage.") from exc
