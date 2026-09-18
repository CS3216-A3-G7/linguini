"""Language-profile checks against a migrated, dedicated test PostgreSQL database."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, insert
from sqlalchemy.exc import IntegrityError, OperationalError

from app.database import create_database_engine, get_language_profile_storage
from app.import_language_profiles import import_language_profiles
from app.main import create_app
from app.repositories.implementations.postgres.language_profiles import (
    PostgresLanguageProfileRepository,
    language_profiles,
)
from app.repositories.implementations.postgres.users import users
from app.repositories.language_profiles import (
    LanguageProfileConflictError,
    LanguageProfileNotFoundError,
    LanguageProfileStorageError,
)
from app.schemas.users import LanguageProfile, UpdateLanguageProfileRequest, User


def test_profile_storage_configuration(monkeypatch):
    monkeypatch.delenv("LANGUAGE_PROFILE_STORAGE", raising=False)
    assert get_language_profile_storage() == "json"
    monkeypatch.setenv("LANGUAGE_PROFILE_STORAGE", "invalid")
    with pytest.raises(ValueError, match="LANGUAGE_PROFILE_STORAGE"):
        get_language_profile_storage()
    monkeypatch.setenv("LANGUAGE_PROFILE_STORAGE", "postgres")
    monkeypatch.setenv("USER_STORAGE", "json")
    with pytest.raises(ValueError, match="requires USER_STORAGE"):
        get_language_profile_storage()
    monkeypatch.setenv("USER_STORAGE", "postgres")
    assert get_language_profile_storage() == "postgres"


def profile(user_id, language="es", **kwargs):
    return LanguageProfile(
        user_id=user_id,
        source_language_code="en",
        target_language_code=language,
        proficiency_level="A1",
        daily_goal_minutes=10,
        **kwargs,
    )


def test_storage_errors_are_wrapped():
    engine = MagicMock()
    engine.connect.side_effect = OperationalError("select", {}, Exception("private detail"))
    engine.begin.side_effect = OperationalError("update", {}, Exception("private detail"))
    repository = PostgresLanguageProfileRepository(engine)
    with pytest.raises(LanguageProfileStorageError):
        repository.list_for_user(uuid4())
    with pytest.raises(LanguageProfileStorageError):
        repository.create(profile(uuid4()))
    with pytest.raises(LanguageProfileStorageError):
        repository.update(uuid4(), uuid4(), UpdateLanguageProfileRequest(is_active=True))


@pytest.mark.parametrize("invalid", ["ids", "pairs", "active"])
def test_import_rejects_invalid_source_before_writing(tmp_path, invalid):
    first = profile(uuid4())
    second = first.model_copy()
    if invalid != "ids":
        second.id = uuid4()
    if invalid == "active":
        second.target_language_code = "fr"
    engine = MagicMock()
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps([row.model_dump(mode="json") for row in [first, second]]))
    with pytest.raises(ValueError):
        import_language_profiles(engine, path)
    engine.begin.assert_not_called()


@pytest.fixture
def database(monkeypatch):
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("Requires migrated test PostgreSQL")
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setenv("USER_STORAGE", "postgres")
    monkeypatch.setenv("LANGUAGE_PROFILE_STORAGE", "postgres")
    engine = create_database_engine()
    owners = [User(auth_provider_id=f"test-{uuid4()}", display_name="Test") for _ in range(2)]
    monkeypatch.setenv("DEMO_USER_ID", str(owners[0].id))
    with engine.begin() as connection:
        for owner in owners:
            connection.execute(insert(users).values(**owner.model_dump(by_alias=False)))
    try:
        yield engine, owners
    finally:
        with engine.begin() as connection:
            connection.execute(delete(users).where(users.c.id.in_([owner.id for owner in owners])))
        engine.dispose()


def test_profile_api_switching_and_isolation(database):
    engine, owners = database
    repository = PostgresLanguageProfileRepository(engine)
    spanish = repository.create(profile(owners[0].id))
    other = repository.create(profile(owners[1].id))
    with TestClient(create_app()) as client:
        assert len(client.get("/api/v1/preloaded-scenes").json()) == 6
        response = client.post(
            "/api/v1/me/language-profiles",
            json={
                "sourceLanguageCode": "en",
                "targetLanguageCode": "fr",
                "proficiencyLevel": "B1",
            },
        )
        assert response.status_code == 201
        french = response.json()
        assert client.get("/api/v1/preloaded-scenes").json() == []
        assert client.get("/api/v1/me/vocabulary").json()["items"] == []
        rows = client.get("/api/v1/me/language-profiles").json()
        assert len(rows) == 2 and sum(row["isActive"] for row in rows) == 1
        assert (
            client.patch(
                f"/api/v1/me/language-profiles/{other.id}", json={"isActive": True}
            ).status_code
            == 404
        )
        url = f"/api/v1/me/language-profiles/{spanish.id}"
        response = client.patch(url, json={"isActive": True, "dailyGoalMinutes": None})
        updated = LanguageProfile.model_validate(response.json())
        assert updated.daily_goal_minutes is None
        assert updated.created_at == spanish.created_at
        assert updated.updated_at > spanish.updated_at
        assert len(client.get("/api/v1/preloaded-scenes").json()) == 6
        assert client.patch(url, json={"dailyGoalMinutes": 0}).status_code == 422
        assert client.patch(url, json={"isActive": False}).status_code == 200
        assert client.get("/api/v1/preloaded-scenes").status_code == 409
        assert (
            client.patch(
                f"/api/v1/me/language-profiles/{french['id']}", json={"isActive": True}
            ).status_code
            == 200
        )
    assert repository.list_for_user(owners[1].id)[0].is_active


def test_duplicate_rollback_and_missing(database):
    engine, owners = database
    repository = PostgresLanguageProfileRepository(engine)
    repository.create(profile(owners[0].id))
    french = repository.create(profile(owners[0].id, "fr"))
    with pytest.raises(LanguageProfileConflictError):
        repository.create(profile(owners[0].id, "ES"))
    assert (
        next(row for row in repository.list_for_user(owners[0].id) if row.is_active).id == french.id
    )
    with pytest.raises(LanguageProfileNotFoundError):
        repository.update(owners[0].id, uuid4(), UpdateLanguageProfileRequest(is_active=True))


def test_concurrent_activation(database):
    engine, owners = database
    repository = PostgresLanguageProfileRepository(engine)
    spanish = repository.create(profile(owners[0].id))
    french = repository.create(profile(owners[0].id, "fr"))
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(
            pool.map(
                lambda row: repository.update(
                    owners[0].id, row.id, UpdateLanguageProfileRequest(is_active=True)
                ),
                [spanish, french],
            )
        )
    assert sum(row.is_active for row in repository.list_for_user(owners[0].id)) == 1


def test_import_idempotency_and_rollback(database, tmp_path):
    engine, owners = database
    first = profile(owners[0].id)
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps([first.model_dump(mode="json")]))
    assert import_language_profiles(engine, path) == 1
    repository = PostgresLanguageProfileRepository(engine)
    repository.update(owners[0].id, first.id, UpdateLanguageProfileRequest(daily_goal_minutes=30))
    assert import_language_profiles(engine, path) == 0
    assert repository.list_for_user(owners[0].id)[0].daily_goal_minutes == 30
    # A valid insert before a foreign-key/parent failure must not survive the transaction.
    records = [profile(owners[0].id, "fr", is_active=False), profile(uuid4())]
    path.write_text(json.dumps([row.model_dump(mode="json") for row in records]))
    with pytest.raises(LanguageProfileStorageError):
        import_language_profiles(engine, path)
    assert len(repository.list_for_user(owners[0].id)) == 1
    # Conflicting pair after a valid insert rolls back the whole batch.
    records = [
        profile(owners[0].id, "fr", is_active=False),
        profile(owners[0].id, "ES", is_active=False),
    ]
    path.write_text(json.dumps([row.model_dump(mode="json") for row in records]))
    with pytest.raises(IntegrityError):
        import_language_profiles(engine, path)
    assert len(repository.list_for_user(owners[0].id)) == 1


@pytest.mark.parametrize(
    "patch",
    [
        {"daily_goal_minutes": 241},
        {"proficiency_level": "D1"},
        {"preferred_input_mode": "voice"},
        {"target_language_code": "EN"},
        {"target_language_code": "invalid_code"},
        {"user_id": uuid4()},
    ],
)
def test_database_constraints(database, patch):
    engine, owners = database
    values = profile(owners[0].id).model_dump(by_alias=False) | patch
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(insert(language_profiles).values(**values))


def test_database_active_constraint_and_cascade(database):
    engine, owners = database
    repository = PostgresLanguageProfileRepository(engine)
    repository.create(profile(owners[0].id))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            insert(language_profiles).values(
                **profile(owners[0].id, "fr").model_dump(by_alias=False)
            )
        )
    with engine.begin() as connection:
        connection.execute(delete(users).where(users.c.id == owners[0].id))
    assert repository.list_for_user(owners[0].id) == []
