import json
import os
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import delete, insert, text, update
from sqlalchemy.exc import IntegrityError, OperationalError

from app.api.dependencies import get_media_asset_repository, get_scene_repository
from app.config import DEMO_USERS_PATH
from app.database import create_database_engine, get_media_asset_storage
from app.import_media_assets import import_media_assets
from app.main import create_app
from app.repositories.implementations.json.media_assets import (
    JsonMediaAssetRepository,
    read_media_assets,
)
from app.repositories.implementations.json.scenes import JsonSceneRepository
from app.repositories.implementations.postgres.media_assets import (
    PostgresMediaAssetRepository,
    media_assets,
)
from app.repositories.implementations.postgres.users import users
from app.repositories.media_assets import MediaAssetConflictError, MediaAssetStorageError
from app.schemas.media import MediaAsset
from app.schemas.users import User


def asset(**values):
    return MediaAsset.model_validate(
        {
            "media_type": "image",
            "source": "preloaded",
            "storage_key": f"test/{uuid4()}",
            "mime_type": "image/png",
            **values,
        }
    )


@pytest.mark.parametrize(
    "values",
    [
        {"duration_ms": 1},
        {"width": 0},
        {"height": -1},
        {"mime_type": "audio/mp3"},
        {"mime_type": "image/"},
        {"owner_user_id": uuid4()},
        {"source": "camera"},
        {"source": "userUpload"},
        {"storage_key": " "},
        {"media_type": "audio", "mime_type": "audio/ogg", "width": 10},
    ],
)
def test_invalid_metadata(values):
    with pytest.raises(ValidationError):
        asset(**values)


def test_media_storage_configuration(monkeypatch):
    monkeypatch.delenv("MEDIA_ASSET_STORAGE", raising=False)
    assert get_media_asset_storage() == "json"
    monkeypatch.setenv("MEDIA_ASSET_STORAGE", "invalid")
    with pytest.raises(ValueError):
        get_media_asset_storage()
    monkeypatch.setenv("MEDIA_ASSET_STORAGE", "postgres")
    monkeypatch.setenv("USER_STORAGE", "json")
    with pytest.raises(ValueError, match="requires USER_STORAGE"):
        get_media_asset_storage()
    monkeypatch.setenv("USER_STORAGE", "postgres")
    assert get_media_asset_storage() == "postgres"


def test_json_lookup_and_api():
    path = DEMO_USERS_PATH.parent / "scenes.json"
    records = read_media_assets(path)
    assert len(records) == 6
    assert JsonMediaAssetRepository(path).get_by_ids([records[0].id]) == {records[0].id: records[0]}
    with TestClient(create_app()) as client:
        response = client.get(f"/api/v1/media/{records[0].id}")
        assert response.status_code == 200
        assert response.json() == records[0].model_dump(mode="json")
        assert client.get(f"/api/v1/media/{uuid4()}").status_code == 404


def test_import_deduplicates_shared_asset_and_rejects_conflicts(tmp_path):
    row = asset().model_dump(mode="json")
    path = tmp_path / "scenes.json"
    path.write_text(json.dumps([{"mediaAsset": row}, {"mediaAsset": row}]))
    assert len(read_media_assets(path)) == 1
    path.write_text(json.dumps([{"mediaAsset": row}, {"mediaAsset": row | {"width": 99}}]))
    engine = MagicMock()
    with pytest.raises(ValueError, match="Conflicting"):
        import_media_assets(engine, path)
    engine.begin.assert_not_called()
    path.write_text(json.dumps([row, row | {"id": str(uuid4())}]))
    with pytest.raises(ValueError, match="storage key"):
        import_media_assets(engine, path, from_scenes=False)


def test_storage_errors_are_controlled():
    engine = MagicMock()
    engine.connect.side_effect = OperationalError("select", {}, Exception("private"))
    engine.begin.side_effect = OperationalError("insert", {}, Exception("private"))
    repository = PostgresMediaAssetRepository(engine)
    assert repository.get_by_ids([]) == {}
    with pytest.raises(MediaAssetStorageError):
        repository.create(asset())
    app = create_app()
    app.dependency_overrides[get_media_asset_repository] = lambda: repository
    response = TestClient(app).get(f"/api/v1/media/{uuid4()}")
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "media_asset_storage_error"
    assert "private" not in response.text


@pytest.fixture
def database(monkeypatch):
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("Requires migrated test PostgreSQL")
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setenv("USER_STORAGE", "postgres")
    monkeypatch.setenv("MEDIA_ASSET_STORAGE", "postgres")
    engine = create_database_engine()
    owner = User(display_name="Media test", auth_provider_id=f"test-{uuid4()}")
    monkeypatch.setenv("DEMO_USER_ID", str(owner.id))
    with engine.begin() as connection:
        connection.execute(insert(users).values(**owner.model_dump(by_alias=False)))
    ids = []
    try:
        yield engine, owner, ids
    finally:
        with engine.begin() as connection:
            connection.execute(delete(media_assets).where(media_assets.c.id.in_(ids)))
            connection.execute(delete(users).where(users.c.id == owner.id))
        engine.dispose()


def test_owned_and_shared_lookup(database, monkeypatch):
    engine, owner, ids = database
    repository = PostgresMediaAssetRepository(engine)
    own = asset(source="camera", owner_user_id=owner.id, width=100)
    shared = asset()
    internal = asset(source="generated")
    audio = asset(
        source="userUpload",
        owner_user_id=owner.id,
        media_type="audio",
        mime_type="audio/ogg",
        duration_ms=50,
    )
    for row in [own, shared, internal, audio]:
        ids.append(row.id)
        assert repository.create(row) == row
    with TestClient(create_app()) as client:
        for row in [own, shared, audio]:
            assert client.get(f"/api/v1/media/{row.id}").json() == row.model_dump(mode="json")
        assert client.get(f"/api/v1/media/{internal.id}").status_code == 404
        # Another existing application user cannot read owned metadata.
        other = User(display_name="Other", auth_provider_id=f"test-{uuid4()}")
        with engine.begin() as connection:
            connection.execute(insert(users).values(**other.model_dump(by_alias=False)))
        try:
            monkeypatch.setenv("DEMO_USER_ID", str(other.id))
            assert client.get(f"/api/v1/media/{own.id}").status_code == 404
            assert client.get(f"/api/v1/media/{shared.id}").status_code == 200
        finally:
            with engine.begin() as connection:
                connection.execute(delete(users).where(users.c.id == other.id))
    with pytest.raises(MediaAssetConflictError):
        repository.create(asset(storage_key=shared.storage_key))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(delete(users).where(users.c.id == owner.id))


def test_scene_import_and_database_hydration(database, tmp_path):
    engine, owner, ids = database
    scenes = json.loads((DEMO_USERS_PATH.parent / "scenes.json").read_text(encoding="utf-8"))
    for scene in scenes:
        row = asset().model_dump(mode="json")
        scene["mediaAsset"] = row
        ids.append(MediaAsset.model_validate(row).id)
    path = tmp_path / "scenes.json"
    path.write_text(json.dumps(scenes), encoding="utf-8")
    assert import_media_assets(engine, path) == 6
    assert import_media_assets(engine, path) == 0
    with engine.begin() as connection:
        connection.execute(
            update(media_assets).where(media_assets.c.id == ids[0]).values(width=640)
        )
    app = create_app()
    app.dependency_overrides[get_scene_repository] = lambda: JsonSceneRepository(path)
    with TestClient(app) as client:
        # Active profile still comes from JSON in this incremental configuration.
        from app.api.dependencies import get_active_language

        app.dependency_overrides[get_active_language] = lambda: "es"
        response = client.get("/api/v1/preloaded-scenes")
        assert response.status_code == 200
        assert response.json()[0]["mediaAsset"]["width"] == 640
        assert (
            client.get(f"/api/v1/preloaded-scenes/{scenes[0]['sceneId']}").json()["mediaAsset"][
                "width"
            ]
            == 640
        )
        with engine.begin() as connection:
            connection.execute(delete(media_assets).where(media_assets.c.id == ids[0]))
        assert client.get("/api/v1/preloaded-scenes").status_code == 500
    # Import a valid new row then a conflicting key: the new row must roll back.
    fresh = asset()
    conflicting = asset(storage_key=scenes[1]["mediaAsset"]["storageKey"])
    ids.extend([fresh.id, conflicting.id])
    path.write_text(
        json.dumps([fresh.model_dump(mode="json"), conflicting.model_dump(mode="json")])
    )
    with pytest.raises(IntegrityError):
        import_media_assets(engine, path, from_scenes=False)
    assert PostgresMediaAssetRepository(engine).get_by_ids([fresh.id]) == {}


@pytest.mark.parametrize(
    "patch",
    [
        {"width": 0},
        {"height": -1},
        {"duration_ms": 1},
        {"mime_type": "audio/ogg"},
        {"mime_type": "image/"},
        {"source": "camera"},
        {"source": "userUpload"},
        {"owner_user_id": uuid4()},
        {"media_type": "audio", "mime_type": "audio/ogg", "width": 1},
        {"media_type": "audio", "mime_type": "audio/ogg", "duration_ms": 0},
        {"storage_key": " "},
        {"source": "unknown"},
        {"owner_user_id": uuid4(), "source": "generated"},
    ],
)
def test_database_constraints(database, patch):
    engine, _, _ = database
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            insert(media_assets).values(**(asset().model_dump(by_alias=False) | patch))
        )


def test_database_timestamp_and_rls(database):
    engine, _, ids = database
    row = asset()
    ids.append(row.id)
    PostgresMediaAssetRepository(engine).create(row)
    with engine.begin() as connection:
        before_update = connection.execute(text("SELECT clock_timestamp()")).scalar_one()
        updated = (
            connection.execute(
                update(media_assets)
                .where(media_assets.c.id == row.id)
                .values(width=99)
                .returning(media_assets)
            )
            .mappings()
            .one()
        )
        after_update = connection.execute(text("SELECT clock_timestamp()")).scalar_one()
        # Host and Docker clocks can differ; validate the trigger against the DB clock.
        assert before_update <= updated["updated_at"] <= after_update
        assert updated["created_at"] == row.created_at
        assert connection.execute(
            text("SELECT relrowsecurity FROM pg_class WHERE oid = 'public.media_assets'::regclass")
        ).scalar_one()
