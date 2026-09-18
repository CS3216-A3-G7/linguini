import os
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, insert, update
from sqlalchemy.exc import IntegrityError

from app.database import create_database_engine
from app.main import create_app
from app.repositories.postgres.language_profiles import (
    PostgresLanguageProfileRepository,
)
from app.repositories.postgres.practice import PostgresPracticeRepository, sessions
from app.repositories.postgres.scene_objects import (
    PostgresSceneObjectRepository,
    scene_objects,
)
from app.repositories.postgres.users import users
from app.repositories.practice import PracticeStorageError
from app.schemas.media import SceneObject
from app.schemas.users import LanguageProfile, User


@pytest.fixture
def database(monkeypatch):
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("Requires migrated test PostgreSQL")
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    engine = create_database_engine()
    owner = User(display_name="Sessions test", auth_provider_id=f"test-{uuid4()}")
    monkeypatch.setenv("DEMO_USER_ID", str(owner.id))
    with engine.begin() as connection:
        connection.execute(insert(users).values(**owner.model_dump(by_alias=False)))
    profile = PostgresLanguageProfileRepository(engine).create(
        LanguageProfile(
            user_id=owner.id,
            source_language_code="en",
            target_language_code="es",
            proficiency_level="A1",
        )
    )
    with TestClient(create_app()) as client:
        yield engine, owner, profile, client
    with engine.begin() as connection:
        connection.execute(delete(users).where(users.c.id == owner.id))
    engine.dispose()


def create_run(client, profile, key="session-key-1"):
    scenes = client.get("/api/v1/preloaded-scenes").json()
    scene = next(row for row in scenes if row.get("languageCode", "es") == "es")
    response = client.post(
        "/api/v1/sessions",
        json={
            "languageProfileId": str(profile.id),
            "mediaAssetId": scene["mediaAsset"]["id"],
            "idempotencyKey": key,
        },
    )
    assert response.status_code == 202, response.text
    return response.json()


def test_sessions_persist_idempotently_and_xp_is_atomic(database):
    engine, owner, profile, client = database
    run = create_run(client, profile)
    session_id = run["session"]["id"]
    assert create_run(client, profile)["session"]["id"] == session_id

    def score(_):
        return client.post(
            f"/api/v1/sessions/{session_id}/demo-events",
            json={"kind": "analysis", "itemId": "analysis"},
        )

    with ThreadPoolExecutor(max_workers=8) as workers:
        responses = list(workers.map(score, range(8)))
    assert all(row.status_code == 200 for row in responses)
    repository = PostgresPracticeRepository(engine, owner.id)
    assert repository.read()[0].xp == 12
    with TestClient(create_app()) as restarted:
        assert (
            restarted.get(f"/api/v1/sessions/{session_id}").json()["demoState"]["sessionXp"] == 12
        )
        assert restarted.get("/api/v1/me/progress").json()["xp"] == 12
    replacement = create_run(client, profile, "session-key-2")
    assert replacement["session"]["id"] != session_id
    assert client.get(f"/api/v1/sessions/{session_id}").json()["session"]["status"] == "abandoned"
    assert (
        client.post(f"/api/v1/sessions/{replacement['session']['id']}/abandon").status_code == 200
    )
    assert client.get("/api/v1/sessions/active").json() is None


def test_review_objects_is_scoped_and_rolls_back(database):
    engine, owner, profile, client = database
    run = create_run(client, profile)["session"]
    item = SceneObject(
        session_id=run["id"],
        media_asset_id=run["sceneMediaAssetId"],
        detected_label="cup",
        bounding_box={"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4},
    )
    repository = PostgresSceneObjectRepository(engine)
    repository.create(item)
    endpoint = f"/api/v1/sessions/{run['id']}/scene-objects"
    correction = {
        "sceneObjectId": str(item.id),
        "selectionStatus": "corrected",
        "confirmedLabel": "mug",
    }
    response = client.patch(endpoint, json={"objects": [correction]})
    assert response.status_code == 200, response.text
    assert response.json()["sceneObjects"][0]["confirmedLabel"] == "mug"
    correction["confirmedLabel"] = "must rollback"
    response = client.patch(
        endpoint,
        json={
            "objects": [correction, {"sceneObjectId": str(uuid4()), "selectionStatus": "accepted"}]
        },
    )
    assert response.status_code == 404
    assert repository.list_for_session(UUID(run["id"]), owner.id)[0].confirmed_label == "mug"
    assert repository.list_for_session(UUID(run["id"]), uuid4()) == []
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            update(scene_objects).where(scene_objects.c.id == item.id).values(width=1)
        )
    client.post(f"/api/v1/sessions/{run['id']}/abandon")
    assert client.patch(endpoint, json={"objects": [correction]}).status_code == 409


def test_invalid_session_rolls_back_xp_and_enforces_owner(database):
    engine, owner, profile, client = database
    create_run(client, profile)
    repository = PostgresPracticeRepository(engine, owner.id)

    def corrupt(rows):
        rows[0].xp = 999
        rows[0].practice_sessions[0].session.scene_media_asset_id = uuid4()

    with pytest.raises(PracticeStorageError):
        repository.change(corrupt)
    assert repository.read()[0].xp == 0
    run = repository.read()[0].practice_sessions[0]
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            update(sessions).where(sessions.c.id == run.session.id).values(user_id=uuid4())
        )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            update(sessions).where(sessions.c.id == run.session.id).values(status="completed")
        )


def test_complete_session_and_replay(database):
    engine, owner, profile, client = database
    detail = create_run(client, profile)
    sid = detail["session"]["id"]
    scene = client.get(f"/api/v1/preloaded-scenes/{detail['demoState']['sceneId']}").json()
    endpoint = f"/api/v1/sessions/{sid}"
    assert client.post(endpoint + "/complete").status_code == 409
    events = [{"kind": "analysis"}]
    events += [{"kind": "task", "itemId": task["id"]} for task in scene["tasks"]]
    events += [
        {"kind": "round", "itemId": row["id"], "answerId": row["choices"][0]["id"]}
        for row in scene["rounds"]
    ]
    events += [{"kind": "clue", "itemId": row["id"], "text": "My clue"} for row in scene["prompts"]]
    for event in events:
        response = client.post(endpoint + "/demo-events", json=event)
        assert response.status_code == 200, response.text
    first = client.post(endpoint + "/complete")
    assert first.status_code == 200, first.text
    assert first.json()["completedAt"] is not None
    assert client.post(endpoint + "/complete").json() == first.json()
    assert client.post(endpoint + "/abandon").status_code == 409
    assert PostgresPracticeRepository(engine, owner.id).read()[0].scenarios[0].status == "completed"
