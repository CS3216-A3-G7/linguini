import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from encounter_factory import create_encounter_task
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.exc import IntegrityError, OperationalError

from app.database import create_database_engine
from app.main import create_app
from app.repositories.learning import LearningStorageError
from app.repositories.postgres.language_profiles import (
    PostgresLanguageProfileRepository,
)
from app.repositories.postgres.media_assets import (
    PostgresMediaAssetRepository,
    media_assets,
)
from app.repositories.postgres.practice import sessions
from app.repositories.postgres.tasks import entity_values, session_tasks
from app.repositories.postgres.users import users
from app.repositories.postgres.vocabulary import (
    PostgresVocabularyRepository,
    VocabularyEncounterConflictError,
    user_vocabulary_progress,
    vocabulary_encounters,
    vocabulary_items,
    vocabulary_translations,
)
from app.schemas.media import MediaAsset
from app.schemas.tasks import SessionTask
from app.schemas.users import LanguageProfile, User
from app.schemas.vocabulary import (
    UserVocabularyProgress,
    VocabularyEncounter,
    VocabularyTranslation,
)


def test_progress_count_validation():
    with pytest.raises(ValidationError):
        UserVocabularyProgress(user_id=uuid4(), vocabulary_item_id=uuid4(), correct_attempt_count=1)


def test_storage_errors():
    engine = MagicMock()
    engine.connect.side_effect = OperationalError("select", {}, Exception("secret"))
    repository = PostgresVocabularyRepository(engine)
    with pytest.raises(LearningStorageError):
        repository.list_vocabulary(uuid4())


@pytest.fixture
def database(monkeypatch):
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("Requires migrated test PostgreSQL")
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    engine = create_database_engine()
    owner = User(display_name="Vocabulary test", auth_provider_id=f"test-{uuid4()}")
    monkeypatch.setenv("DEMO_USER_ID", str(owner.id))
    with engine.begin() as connection:
        connection.execute(insert(users).values(**owner.model_dump(by_alias=False)))
    PostgresLanguageProfileRepository(engine).create(
        LanguageProfile(
            user_id=owner.id,
            source_language_code="en",
            target_language_code="es",
            proficiency_level="A1",
        )
    )
    ids = []
    media_ids = []
    from app.schemas.vocabulary import VocabularyItem

    with engine.begin() as connection:
        for word in ["calle", "autobus", "arbol"]:
            item = VocabularyItem(
                language_code="es", lemma=word, display_text=word, part_of_speech="noun"
            )
            ids.append(item.id)
            translation = VocabularyTranslation(
                vocabulary_item_id=item.id,
                source_language_code="en",
                translated_text=f"Translation of {word}",
            )
            progress = UserVocabularyProgress(user_id=owner.id, vocabulary_item_id=item.id)
            connection.execute(insert(vocabulary_items).values(**item.model_dump(by_alias=False)))
            connection.execute(
                insert(vocabulary_translations).values(**translation.model_dump(by_alias=False))
            )
            connection.execute(
                insert(user_vocabulary_progress).values(
                    **progress.model_dump(by_alias=False), scene_id="calle-mayor", topic="City"
                )
            )
    repository = PostgresVocabularyRepository(engine)
    try:
        yield engine, owner, ids, media_ids, repository
    finally:
        with engine.begin() as connection:
            connection.execute(delete(users).where(users.c.id == owner.id))
            connection.execute(delete(vocabulary_items).where(vocabulary_items.c.id.in_(ids)))
            connection.execute(delete(media_assets).where(media_assets.c.id.in_(media_ids)))
        engine.dispose()


def test_api_pagination_translation_and_isolation(database, monkeypatch):
    engine, owner, ids, _, repository = database
    with TestClient(create_app()) as client:
        first = client.get("/api/v1/me/vocabulary?limit=2")
        assert first.status_code == 200
        page = first.json()
        assert len(page["items"]) == 2 and page["nextCursor"]
        second = client.get(
            "/api/v1/me/vocabulary", params={"cursor": page["nextCursor"], "limit": 2}
        ).json()
        assert len(second["items"]) == 1 and second["nextCursor"] is None
        assert len({row["vocabulary"]["id"] for row in page["items"] + second["items"]}) == 3
        assert all(row["sceneId"] and row["topic"] for row in page["items"])
        assert client.get("/api/v1/me/vocabulary?cursor=invalid").status_code == 400
        other = User(display_name="Other", auth_provider_id=f"test-{uuid4()}")
        with engine.begin() as connection:
            connection.execute(insert(users).values(**other.model_dump(by_alias=False)))
        try:
            PostgresLanguageProfileRepository(engine).create(
                LanguageProfile(
                    user_id=other.id,
                    source_language_code="en",
                    target_language_code="es",
                    proficiency_level="A1",
                )
            )
            assert repository.list_vocabulary(other.id) == []
            monkeypatch.setenv("DEMO_USER_ID", str(other.id))
            assert client.get("/api/v1/me/vocabulary").json()["items"] == []
        finally:
            with engine.begin() as connection:
                connection.execute(delete(users).where(users.c.id == other.id))
    french = VocabularyTranslation(
        vocabulary_item_id=ids[0], source_language_code="FR", translated_text="rue"
    )
    with engine.begin() as connection:
        connection.execute(
            insert(vocabulary_translations).values(**french.model_dump(by_alias=False))
        )
    PostgresLanguageProfileRepository(engine).create(
        LanguageProfile(
            user_id=owner.id,
            source_language_code="fr",
            target_language_code="es",
            proficiency_level="A1",
        )
    )
    words = repository.list_vocabulary(owner.id)
    assert (
        next(row for row in words if row.vocabulary.id == ids[0]).translation.translated_text
        == "rue"
    )
    assert sum(row.translation is None for row in words) == 2
    PostgresLanguageProfileRepository(engine).create(
        LanguageProfile(
            user_id=owner.id,
            source_language_code="en",
            target_language_code="de",
            proficiency_level="A1",
        )
    )
    assert repository.list_vocabulary(owner.id) == []


@pytest.fixture
def encounter_task(database):
    engine, owner, *_ = database
    profile = PostgresLanguageProfileRepository(engine).list_for_user(owner.id)[0]
    with TestClient(create_app()) as client:
        return create_encounter_task(engine, client, profile)


def test_concurrent_encounters_are_idempotent_and_atomic(database, encounter_task):
    engine, owner, ids, _, repository = database
    event = VocabularyEncounter(
        user_id=owner.id,
        vocabulary_item_id=ids[0],
        session_id=encounter_task.session_id,
        session_task_id=encounter_task.id,
        encounter_type="practised",
        outcome="correct",
    )
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(repository.record_encounter, [event] * 8))
    word = next(row for row in repository.list_vocabulary(owner.id) if row.vocabulary.id == ids[0])
    assert word.encounter_ids == [event.id]
    assert word.progress.exposure_count == word.progress.correct_attempt_count == 1
    assert word.progress.last_practised_at == event.occurred_at
    assert word.progress.first_learned_at == event.occurred_at
    with pytest.raises(VocabularyEncounterConflictError):
        repository.record_encounter(
            VocabularyEncounter.model_validate(
                event.model_dump(by_alias=False) | {"outcome": "incorrect"}
            )
        )
    more = [event.model_copy(update={"id": uuid4()}) for _ in range(8)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(repository.record_encounter, more))
    word = next(row for row in repository.list_vocabulary(owner.id) if row.vocabulary.id == ids[0])
    assert word.progress.exposure_count == word.progress.correct_attempt_count == 9
    assert len(word.encounter_ids) == 9
    assert (
        next(
            row for row in repository.list_vocabulary(owner.id) if row.vocabulary.id == ids[0]
        ).progress.exposure_count
        == 9
    )
    unknown = uuid4()
    with pytest.raises(LearningStorageError):
        repository.record_encounter(
            event.model_copy(update={"id": uuid4(), "vocabulary_item_id": unknown})
        )
    with engine.connect() as connection:
        assert (
            connection.execute(
                select(user_vocabulary_progress).where(
                    user_vocabulary_progress.c.vocabulary_item_id == unknown
                )
            ).first()
            is None
        )


@pytest.mark.parametrize(
    "patch",
    [
        {"status": "bad"},
        {"exposure_count": -1},
        {"correct_attempt_count": -1},
        {"correct_attempt_count": 1},
        {"mastery_score": Decimal("1.1")},
    ],
)
def test_progress_constraints(database, patch):
    engine, _, ids, _, _ = database
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            update(user_vocabulary_progress)
            .where(user_vocabulary_progress.c.vocabulary_item_id == ids[0])
            .values(**patch)
        )


def test_relations_uniqueness_and_rls(database):
    engine, owner, ids, _, _ = database
    duplicate = VocabularyTranslation(
        vocabulary_item_id=ids[0], source_language_code="EN", translated_text="duplicate"
    )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            insert(vocabulary_translations).values(**duplicate.model_dump(by_alias=False))
        )
    duplicate_progress = UserVocabularyProgress(user_id=owner.id, vocabulary_item_id=ids[0])
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            insert(user_vocabulary_progress).values(**duplicate_progress.model_dump(by_alias=False))
        )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(delete(vocabulary_items).where(vocabulary_items.c.id == ids[0]))
    with engine.connect() as connection:
        for table in [
            vocabulary_items,
            vocabulary_translations,
            user_vocabulary_progress,
            vocabulary_encounters,
        ]:
            assert connection.execute(
                text("SELECT relrowsecurity FROM pg_class WHERE oid = CAST(:name AS regclass)"),
                {"name": f"public.{table.name}"},
            ).scalar_one()


def test_pronunciation_audio_relation(database):
    engine, _, ids, media_ids, _ = database
    audio = MediaAsset(
        media_type="audio", source="preloaded", mime_type="audio/ogg", storage_key=f"test/{uuid4()}"
    )
    image = MediaAsset(
        media_type="image", source="preloaded", mime_type="image/png", storage_key=f"test/{uuid4()}"
    )
    for asset in [audio, image]:
        media_ids.append(asset.id)
        PostgresMediaAssetRepository(engine).create(asset)
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            update(vocabulary_items)
            .where(vocabulary_items.c.id == ids[0])
            .values(pronunciation_audio_asset_id=image.id)
        )
    with engine.begin() as connection:
        connection.execute(
            update(vocabulary_items)
            .where(vocabulary_items.c.id == ids[0])
            .values(pronunciation_audio_asset_id=audio.id)
        )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            update(media_assets)
            .where(media_assets.c.id == audio.id)
            .values(media_type="image", mime_type="image/png")
        )
    with engine.begin() as connection:
        connection.execute(delete(media_assets).where(media_assets.c.id == audio.id))
        assert (
            connection.execute(
                select(vocabulary_items.c.pronunciation_audio_asset_id).where(
                    vocabulary_items.c.id == ids[0]
                )
            ).scalar_one()
            is None
        )


@pytest.mark.parametrize(
    "patch",
    [
        {"outcome": "invalid"},
        {"encounter_type": "invalid"},
        {"user_id": uuid4()},
        {"vocabulary_item_id": uuid4()},
        {"session_id": None},
    ],
)
def test_encounter_database_constraints(database, encounter_task, patch):
    engine, owner, ids, _, _ = database
    event = VocabularyEncounter(
        user_id=owner.id,
        vocabulary_item_id=ids[0],
        session_id=encounter_task.session_id,
        session_task_id=encounter_task.id,
        encounter_type="introduced",
        outcome="completed",
    )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            insert(vocabulary_encounters).values(**(event.model_dump(by_alias=False) | patch))
        )


@pytest.mark.parametrize(
    "invalid", ["missing_session", "missing_task", "other_session", "other_user"]
)
def test_encounter_parent_links_and_counter_rollback(
    database, encounter_task, monkeypatch, invalid
):
    engine, owner, ids, _, repository = database
    other = User(display_name="Other", auth_provider_id=f"test-{uuid4()}")
    event = VocabularyEncounter(
        user_id=owner.id,
        vocabulary_item_id=ids[0],
        session_id=encounter_task.session_id,
        session_task_id=encounter_task.id,
        encounter_type="practised",
        outcome="correct",
    )
    expected_constraint = "vocabulary_encounters_task_session_fkey"
    if invalid == "missing_session":
        event.session_id = uuid4()
        expected_constraint = "vocabulary_encounters_session_owner_fkey"
    elif invalid == "missing_task":
        event.session_task_id = uuid4()
    elif invalid == "other_session":
        with engine.begin() as connection:
            copied = dict(
                connection.execute(
                    select(sessions).where(sessions.c.id == encounter_task.session_id)
                )
                .mappings()
                .one()
            )
            # Terminal status avoids the one-active-session index; only the
            # (task, session) pairing needs to be invalid here.
            copied.update(id=uuid4(), status="failed", idempotency_key=None)
            connection.execute(insert(sessions).values(**copied))
            other_task = SessionTask(
                session_id=copied["id"],
                phase="learning",
                kind="grammarPractice",
                order_index=0,
                public_content={
                    "kind": "grammarPractice",
                    "prompt": "Choose",
                    "options": ["uno", "dos"],
                },
            )
            connection.execute(insert(session_tasks).values(**entity_values(other_task)))
        event.session_task_id = other_task.id
    else:
        # A valid progress pair ensures the new owner FK, rather than the old progress FK,
        # is what rejects the reference to someone else's existing session and task.
        with engine.begin() as connection:
            connection.execute(insert(users).values(**other.model_dump(by_alias=False)))
            progress = UserVocabularyProgress(user_id=other.id, vocabulary_item_id=ids[0])
            connection.execute(
                insert(user_vocabulary_progress).values(**progress.model_dump(by_alias=False))
            )
        event.user_id = other.id
        expected_constraint = "vocabulary_encounters_session_owner_fkey"
    try:
        with pytest.raises(IntegrityError) as error, engine.begin() as connection:
            connection.execute(
                insert(vocabulary_encounters).values(**event.model_dump(by_alias=False))
            )
        assert error.value.orig.diag.constraint_name == expected_constraint
        with pytest.raises(LearningStorageError):
            repository.record_encounter(event)
        with engine.connect() as connection:
            progress = (
                connection.execute(
                    select(user_vocabulary_progress).where(
                        user_vocabulary_progress.c.user_id == event.user_id,
                        user_vocabulary_progress.c.vocabulary_item_id == ids[0],
                    )
                )
                .mappings()
                .one()
            )
            assert progress["exposure_count"] == progress["correct_attempt_count"] == 0
            assert (
                connection.execute(
                    select(vocabulary_encounters).where(vocabulary_encounters.c.id == event.id)
                ).first()
                is None
            )
    finally:
        if invalid == "other_user":
            with engine.begin() as connection:
                connection.execute(delete(users).where(users.c.id == other.id))


@pytest.mark.parametrize("parent", ["session", "task", "user"])
def test_encounter_links_cascade_deletion(database, encounter_task, parent):
    from app.repositories.postgres.practice import sessions
    from app.repositories.postgres.tasks import session_tasks

    engine, owner, ids, _, repository = database
    event = repository.record_encounter(
        VocabularyEncounter(
            user_id=owner.id,
            vocabulary_item_id=ids[0],
            session_id=encounter_task.session_id,
            session_task_id=encounter_task.id,
            encounter_type="introduced",
            outcome="completed",
        )
    )
    for field in ["session_id", "session_task_id"]:
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(
                update(vocabulary_encounters)
                .where(vocabulary_encounters.c.id == event.id)
                .values(**{field: uuid4()})
            )
    with engine.begin() as connection:
        table, parent_id = {
            "session": (sessions, event.session_id),
            "task": (session_tasks, event.session_task_id),
            "user": (users, owner.id),
        }[parent]
        connection.execute(delete(table).where(table.c.id == parent_id))
    with engine.connect() as connection:
        assert (
            connection.execute(
                select(vocabulary_encounters).where(vocabulary_encounters.c.id == event.id)
            ).first()
            is None
        )

        if parent != "user":
            progress = connection.execute(select(user_vocabulary_progress).where(
                user_vocabulary_progress.c.user_id == owner.id,
                user_vocabulary_progress.c.vocabulary_item_id == ids[0],
            )).mappings().one()
            assert progress["exposure_count"] == progress["correct_attempt_count"] == 0
            assert progress["first_learned_at"] is None
            assert connection.execute(
                select(vocabulary_items.c.id).where(vocabulary_items.c.id == ids[0])
            ).first()
