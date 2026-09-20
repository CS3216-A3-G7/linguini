from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.exc import IntegrityError, OperationalError
from test_postgres_sessions import database as database

from app.repositories.postgres.media_assets import media_assets
from app.repositories.postgres.scenes import (
    PostgresSceneRepository,
    preloaded_scenes,
)
from app.repositories.scenes import SceneStorageError
from app.schemas.scenes import PreloadedSceneDetail


def store_scene(connection, scene):
    connection.execute(insert(media_assets).values(**scene.media_asset.model_dump(by_alias=False)))
    values = scene.model_dump(
        by_alias=False,
        exclude={"items", "tasks", "rounds", "prompts", "media_asset", "scene_id", "image_url"},
    )
    connection.execute(
        insert(preloaded_scenes).values(
            **values,
            slug=scene.scene_id,
            media_asset_id=scene.media_asset.id,
            content=scene.model_dump(
                mode="json", by_alias=True, include={"items", "tasks", "rounds", "prompts"}
            ),
        )
    )


@pytest.fixture
def source(database):
    engine, *_ = database
    row = PostgresSceneRepository(engine).list_scenes()[0].model_dump(mode="json", by_alias=True)
    row["sceneId"] = f"test-{uuid4()}"
    row["mediaAsset"]["id"] = str(uuid4())
    row["mediaAsset"]["storageKey"] = f"test/{uuid4()}"
    return row


@pytest.fixture
def scene_record(database, source):
    engine, _, _, client = database
    row = source
    with engine.begin() as connection:
        store_scene(connection, PreloadedSceneDetail.model_validate(row))
    yield engine, client, row
    with engine.begin() as connection:
        connection.execute(
            delete(preloaded_scenes).where(preloaded_scenes.c.slug == row["sceneId"])
        )
        connection.execute(
            delete(media_assets).where(media_assets.c.id == UUID(row["mediaAsset"]["id"]))
        )


def test_api_and_visibility(scene_record):
    engine, client, row = scene_record
    slug = row["sceneId"]
    response = client.get(f"/api/v1/preloaded-scenes/{slug}")
    assert response.status_code == 200
    expected = PreloadedSceneDetail.model_validate(row).model_dump(mode="json", by_alias=True)
    assert "art" not in response.json()
    for key in ("sceneId", "items", "tasks", "rounds", "prompts", "title"):
        assert response.json()[key] == expected[key]
    with engine.begin() as connection:
        connection.execute(
            update(preloaded_scenes)
            .where(preloaded_scenes.c.slug == slug)
            .values(title="Live edit", sort_order=0, is_active=False)
        )
    assert client.get(f"/api/v1/preloaded-scenes/{slug}").status_code == 404
    with engine.begin() as connection:
        connection.execute(
            update(preloaded_scenes)
            .where(preloaded_scenes.c.slug == slug)
            .values(is_active=True, language_code="fr")
        )
    assert client.get(f"/api/v1/preloaded-scenes/{slug}").status_code == 404
    assert (
        next(r for r in PostgresSceneRepository(engine).list_scenes() if r.scene_id == slug).title
        == "Live edit"
    )


def test_media_integrity_and_rls(scene_record):
    engine, _, row = scene_record
    asset_id = UUID(row["mediaAsset"]["id"])
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(delete(media_assets).where(media_assets.c.id == asset_id))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            update(media_assets).where(media_assets.c.id == asset_id).values(source="generated")
        )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            update(preloaded_scenes)
            .where(preloaded_scenes.c.slug == row["sceneId"])
            .values(media_asset_id=uuid4())
        )
    with engine.connect() as connection:
        assert connection.execute(
            text(
                "SELECT relrowsecurity FROM pg_class WHERE oid='public.preloaded_scenes'::regclass"
            )
        ).scalar_one()


def test_transaction_rolls_back_media_on_invalid_scene(database, source):
    engine, *_ = database
    row = source
    row["languageCode"] = "not a language"
    with pytest.raises(IntegrityError), engine.begin() as connection:
        store_scene(connection, PreloadedSceneDetail.model_validate(row))
    with engine.connect() as connection:
        assert (
            connection.execute(
                select(media_assets.c.id).where(media_assets.c.id == UUID(row["mediaAsset"]["id"]))
            ).first()
            is None
        )


def test_database_errors_are_controlled():
    engine = MagicMock()
    engine.connect.side_effect = OperationalError("select", {}, Exception("private"))
    with pytest.raises(SceneStorageError, match="Unable to load scenes"):
        PostgresSceneRepository(engine).list_scenes()


@pytest.mark.parametrize("invalid", ["duplicate", "reference", "coordinates"])
def test_scene_content_validation(source, invalid):
    if invalid == "duplicate":
        source["items"].append(source["items"][0])
    elif invalid == "reference":
        source["tasks"][0]["itemIds"] = ["unknown"]
    else:
        source["items"][0]["x"] = 101
    with pytest.raises(ValueError):
        PreloadedSceneDetail.model_validate(source)
