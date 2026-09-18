"""Vocabulary persistence; XP/scenario progress continues using its existing store."""

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
    Text,
    Uuid,
    func,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.implementations.postgres.language_profiles import language_profiles
from app.repositories.implementations.postgres.users import users
from app.repositories.learning import LearningRepository, LearningStorageError
from app.schemas.progress import StoredProgress
from app.schemas.vocabulary import (
    DailyVocabularyItem,
    UserVocabularyProgress,
    VocabularyEncounter,
    VocabularyItem,
    VocabularyTranslation,
)

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
    Column("scene_id", Text),
    Column("topic", Text),
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


class PostgresVocabularyRepository:
    def __init__(self, engine: Engine, progress_repository: LearningRepository) -> None:
        self.engine = engine
        self.progress_repository = progress_repository

    def get_progress(
        self, user_id: UUID, language_code: str | None = None
    ) -> StoredProgress | None:
        return self.progress_repository.get_progress(user_id, language_code)

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
                for row in connection.execute(
                    select(vocabulary_encounters)
                    .where(
                        vocabulary_encounters.c.user_id == user_id,
                        vocabulary_encounters.c.vocabulary_item_id.in_(ids),
                    )
                    .order_by(vocabulary_encounters.c.occurred_at, vocabulary_encounters.c.id)
                ).mappings():
                    encounters.setdefault(row["vocabulary_item_id"], []).append(row["id"])
                return [
                    DailyVocabularyItem(
                        vocabulary=items[row["vocabulary_item_id"]],
                        translation=translations.get(row["vocabulary_item_id"]),
                        progress=UserVocabularyProgress.model_validate(
                            {key: row[key] for key in UserVocabularyProgress.model_fields}
                        ),
                        scene_id=row["scene_id"],
                        topic=row["topic"],
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
                initial = UserVocabularyProgress(
                    user_id=encounter.user_id, vocabulary_item_id=encounter.vocabulary_item_id
                )
                connection.execute(
                    insert(user_vocabulary_progress)
                    .values(**initial.model_dump(by_alias=False))
                    .on_conflict_do_nothing(index_elements=["user_id", "vocabulary_item_id"])
                )
                inserted = connection.execute(
                    insert(vocabulary_encounters)
                    .values(**encounter.model_dump(by_alias=False))
                    .on_conflict_do_nothing(index_elements=["id"])
                    .returning(vocabulary_encounters.c.id)
                ).scalar_one_or_none()
                if inserted is None:
                    stored = VocabularyEncounter.model_validate(
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
                    if stored.model_dump(exclude=excluded) != encounter.model_dump(
                        exclude=excluded
                    ):
                        raise VocabularyEncounterConflictError(
                            "Encounter ID already has different data."
                        )
                    return stored
                values = {
                    "exposure_count": user_vocabulary_progress.c.exposure_count + 1,
                    "correct_attempt_count": user_vocabulary_progress.c.correct_attempt_count
                    + int(encounter.outcome.value == "correct"),
                    "first_learned_at": func.least(
                        user_vocabulary_progress.c.first_learned_at, encounter.occurred_at
                    ),
                }
                if encounter.encounter_type.value != "introduced":
                    values["last_practised_at"] = func.greatest(
                        user_vocabulary_progress.c.last_practised_at, encounter.occurred_at
                    )
                connection.execute(
                    update(user_vocabulary_progress)
                    .where(
                        user_vocabulary_progress.c.user_id == encounter.user_id,
                        user_vocabulary_progress.c.vocabulary_item_id
                        == encounter.vocabulary_item_id,
                    )
                    .values(**values)
                )
                return encounter
        except (SQLAlchemyError, ValidationError) as exc:
            raise LearningStorageError("Unable to record vocabulary encounter.") from exc
