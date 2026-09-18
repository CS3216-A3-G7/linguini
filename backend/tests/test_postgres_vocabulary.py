import json
import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.exc import IntegrityError, OperationalError

from app.config import DEMO_USERS_PATH
from app.database import create_database_engine, get_vocabulary_storage
from app.import_vocabulary import import_vocabulary
from app.main import create_app
from app.repositories.implementations.json.learning import JsonLearningRepository
from app.repositories.implementations.postgres.language_profiles import (
    PostgresLanguageProfileRepository,
)
from app.repositories.implementations.postgres.media_assets import (
    PostgresMediaAssetRepository,
    media_assets,
)
from app.repositories.implementations.postgres.users import users
from app.repositories.implementations.postgres.vocabulary import (
    PostgresVocabularyRepository,
    VocabularyEncounterConflictError,
    user_vocabulary_progress,
    vocabulary_encounters,
    vocabulary_items,
    vocabulary_translations,
)
from app.repositories.learning import LearningStorageError
from app.schemas.media import MediaAsset
from app.schemas.users import LanguageProfile, User
from app.schemas.vocabulary import (
    UserVocabularyProgress,
    VocabularyEncounter,
    VocabularyTranslation,
)


def test_configuration(monkeypatch):
    monkeypatch.delenv("VOCABULARY_STORAGE", raising=False)
    assert get_vocabulary_storage() == "json"
    monkeypatch.setenv("VOCABULARY_STORAGE", "invalid")
    with pytest.raises(ValueError):
        get_vocabulary_storage()
    monkeypatch.setenv("VOCABULARY_STORAGE", "postgres")
    monkeypatch.setenv("USER_STORAGE", "json")
    with pytest.raises(ValueError):
        get_vocabulary_storage()
    monkeypatch.setenv("USER_STORAGE", "postgres")
    monkeypatch.setenv("LANGUAGE_PROFILE_STORAGE", "json")
    with pytest.raises(ValueError):
        get_vocabulary_storage()
    monkeypatch.setenv("LANGUAGE_PROFILE_STORAGE", "postgres")
    assert get_vocabulary_storage() == "postgres"


def test_progress_count_validation():
    with pytest.raises(ValidationError):
        UserVocabularyProgress(user_id=uuid4(), vocabulary_item_id=uuid4(), correct_attempt_count=1)


@pytest.mark.parametrize("broken", ["reference", "duplicate", "encounter"])
def test_import_validates_before_write(tmp_path, broken):
    rows = json.loads((DEMO_USERS_PATH.parent / "vocabulary.json").read_text(encoding="utf-8"))[:1]
    if broken == "reference":
        rows[0]["progress"]["vocabularyItemId"] = str(uuid4())
    elif broken == "duplicate":
        second = json.loads(json.dumps(rows[0]))
        second["vocabulary"]["lemma"] = "different"
        rows.append(second)
    else:
        rows[0]["encounterIds"] = [str(uuid4())]
    path = tmp_path / "vocabulary.json"
    path.write_text(json.dumps(rows))
    engine = MagicMock()
    with pytest.raises(ValueError):
        import_vocabulary(engine, path)
    engine.begin.assert_not_called()


def test_storage_errors_and_progress_delegation():
    engine = MagicMock()
    engine.connect.side_effect = OperationalError("select", {}, Exception("secret"))
    fallback = MagicMock()
    repository = PostgresVocabularyRepository(engine, fallback)
    with pytest.raises(LearningStorageError):
        repository.list_vocabulary(uuid4())
    owner = uuid4()
    repository.get_progress(owner, "es")
    fallback.get_progress.assert_called_once_with(owner, "es")


@pytest.fixture
def database(monkeypatch, tmp_path):
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("Requires migrated test PostgreSQL")
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    for key in ["USER_STORAGE", "LANGUAGE_PROFILE_STORAGE", "VOCABULARY_STORAGE"]:
        monkeypatch.setenv(key, "postgres")
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
    rows = json.loads((DEMO_USERS_PATH.parent / "vocabulary.json").read_text(encoding="utf-8"))[:3]
    ids = []
    media_ids = []
    for row in rows:
        item_id = uuid4()
        ids.append(item_id)
        row["vocabulary"]["id"] = str(item_id)
        for field in ["translation", "progress"]:
            row[field]["id"] = str(uuid4())
            row[field]["vocabularyItemId"] = str(item_id)
        row["progress"]["userId"] = str(owner.id)
    path = tmp_path / "vocabulary.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    repository = PostgresVocabularyRepository(
        engine, JsonLearningRepository(DEMO_USERS_PATH.parent)
    )
    try:
        yield engine, owner, ids, media_ids, path, repository
    finally:
        with engine.begin() as connection:
            connection.execute(delete(users).where(users.c.id == owner.id))
            connection.execute(delete(vocabulary_items).where(vocabulary_items.c.id.in_(ids)))
            connection.execute(delete(media_assets).where(media_assets.c.id.in_(media_ids)))
        engine.dispose()


def test_import_api_pagination_translation_and_isolation(database, monkeypatch):
    engine, owner, ids, _, path, repository = database
    assert import_vocabulary(engine, path) == {
        "vocabulary_items": 3,
        "vocabulary_translations": 3,
        "user_vocabulary_progress": 3,
        "vocabulary_encounters": 0,
    }
    assert all(count == 0 for count in import_vocabulary(engine, path).values())
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


def test_concurrent_encounters_are_idempotent_and_atomic(database):
    engine, owner, ids, _, path, repository = database
    import_vocabulary(engine, path)
    event = VocabularyEncounter(
        user_id=owner.id,
        vocabulary_item_id=ids[0],
        session_id=uuid4(),
        session_task_id=uuid4(),
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
    assert all(count == 0 for count in import_vocabulary(engine, path).values())
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


def test_history_import_and_failure_rollback(database, tmp_path):
    engine, owner, ids, _, path, repository = database
    rows = json.loads(path.read_text())
    event = VocabularyEncounter(
        user_id=owner.id,
        vocabulary_item_id=ids[0],
        session_id=uuid4(),
        session_task_id=uuid4(),
        encounter_type="introduced",
        outcome="completed",
    )
    rows[0]["encounterIds"] = [str(event.id)]
    path.write_text(json.dumps(rows))
    history = tmp_path / "encounters.json"
    history.write_text(json.dumps([event.model_dump(mode="json")]))
    assert import_vocabulary(engine, path, history)["vocabulary_encounters"] == 1
    assert next(
        row for row in repository.list_vocabulary(owner.id) if row.vocabulary.id == ids[0]
    ).encounter_ids == [event.id]
    # Import snapshots preserve counters rather than replaying history over the snapshots.
    assert all(row.progress.exposure_count == 0 for row in repository.list_vocabulary(owner.id))
    for row in rows:
        row["encounterIds"] = []
        new_id = uuid4()
        ids.append(new_id)
        row["vocabulary"]["id"] = str(new_id)
        for field in ["translation", "progress"]:
            row[field]["id"] = str(uuid4())
            row[field]["vocabularyItemId"] = str(new_id)
    rows[-1]["progress"]["userId"] = str(uuid4())
    path.write_text(json.dumps(rows))
    with pytest.raises(IntegrityError):
        import_vocabulary(engine, path)
    with engine.connect() as connection:
        assert (
            connection.execute(
                select(vocabulary_items).where(vocabulary_items.c.id == ids[-3])
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
    engine, _, ids, _, path, _ = database
    import_vocabulary(engine, path)
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            update(user_vocabulary_progress)
            .where(user_vocabulary_progress.c.vocabulary_item_id == ids[0])
            .values(**patch)
        )


def test_relations_uniqueness_and_rls(database):
    engine, owner, ids, _, path, _ = database
    import_vocabulary(engine, path)
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
    engine, _, ids, media_ids, path, _ = database
    import_vocabulary(engine, path)
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
def test_encounter_database_constraints(database, patch):
    engine, owner, ids, _, path, _ = database
    import_vocabulary(engine, path)
    event = VocabularyEncounter(
        user_id=owner.id,
        vocabulary_item_id=ids[0],
        session_id=uuid4(),
        session_task_id=uuid4(),
        encounter_type="introduced",
        outcome="completed",
    )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            insert(vocabulary_encounters).values(**(event.model_dump(by_alias=False) | patch))
        )
