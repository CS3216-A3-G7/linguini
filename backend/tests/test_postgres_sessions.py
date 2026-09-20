import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.exc import IntegrityError

from app.database import create_database_engine
from app.main import create_app
from app.repositories.postgres.language_profiles import (
    PostgresLanguageProfileRepository,
)
from app.repositories.postgres.media_assets import media_assets
from app.repositories.postgres.practice import sessions
from app.repositories.postgres.tasks import entity_values, session_tasks, task_attempts
from app.repositories.postgres.users import users
from app.repositories.postgres.vocabulary import user_vocabulary_progress, vocabulary_encounters
from app.repositories.postgres.workflow import PostgresWorkflowRepository
from app.schemas.base import utc_now
from app.schemas.enums import TaskKind
from app.schemas.media import MediaAsset
from app.schemas.tasks import TaskAttempt
from app.schemas.users import LanguageProfile, User


@pytest.fixture
def database(monkeypatch):
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("Requires migrated test PostgreSQL")
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    engine = create_database_engine()
    if os.getenv("TEST_DATABASE_SCHEMA"):
        engine = engine.execution_options(
            schema_translate_map={"public": os.environ["TEST_DATABASE_SCHEMA"]}
        )
        monkeypatch.setattr("app.main.create_database_engine", lambda: engine)
    monkeypatch.setenv("MEDIA_STORAGE_PRIVATE", "false")
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
    app = create_app()
    # Surface the underlying database error in tests instead of a generic HTTP 500.
    from app.repositories.practice import PracticeStorageError

    async def storage_failure(_request, exc):
        raise exc

    app.add_exception_handler(PracticeStorageError, storage_failure)
    with TestClient(app) as client:
        yield engine, owner, profile, client
    with engine.begin() as connection:
        connection.execute(delete(sessions).where(sessions.c.user_id == owner.id))
        connection.execute(delete(media_assets).where(media_assets.c.owner_user_id == owner.id))
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


def analyze(client, sid, confirm=True):
    response = client.post(f"/api/v1/sessions/{sid}/analyze")
    assert response.status_code == 200, response.text
    detail = response.json()
    if confirm and not detail["tasks"]:
        response = client.put(
            f"/api/v1/sessions/{sid}/review",
            json={"acceptedObjectIds": [detail["sceneObjects"][0]["id"]]},
        )
        assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("source", ["preloaded", "userUpload", "camera"])
def test_normalized_workflow_and_idempotent_progress(database, source):
    engine, owner, profile, client = database
    if source == "preloaded":
        run = create_run(client, profile)
        assert create_run(client, profile)["session"]["id"] == run["session"]["id"]
    else:
        asset = MediaAsset(
            owner_user_id=owner.id,
            source=source,
            media_type="image",
            storage_key=f"users/{owner.id}/images/{uuid4()}.jpg",
            mime_type="image/jpeg",
        )
        with engine.begin() as c:
            c.execute(insert(media_assets).values(**asset.model_dump(by_alias=False)))
        response = client.post(
            "/api/v1/sessions",
            json={
                "languageProfileId": str(profile.id),
                "mediaAssetId": str(asset.id),
                "idempotencyKey": "upload-session-key",
            },
        )
        assert response.status_code == 202, response.text
        run = response.json()
    sid = run["session"]["id"]
    endpoint = f"/api/v1/sessions/{sid}"
    assert run["tasks"] == []
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: analyze(client, sid, confirm=False), range(4)))
    assert all(not result["tasks"] for result in results)
    assert all(result["sceneObjects"] == results[0]["sceneObjects"] for result in results)
    detail = analyze(client, sid)
    assert len(detail["tasks"]) == len(TaskKind)
    assert {t["kind"] for t in detail["tasks"]} == {k.value for k in TaskKind}
    assert all(
        o["selectionStatus"] == "accepted" and o["vocabularyItemId"] for o in detail["sceneObjects"]
    )
    assert "answerKey" not in str(detail) and "demoState" not in detail
    assert client.get("/api/v1/me/progress").json()["xp"] == 0
    assert client.post(endpoint + "/complete").status_code == 409
    tasks = detail["tasks"]
    intro = tasks[0]["id"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        completed = list(
            pool.map(lambda _: client.post(f"/api/v1/tasks/{intro}/complete"), range(4))
        )
    assert all(r.status_code == 200 for r in completed)
    pronunciation = tasks[1]
    answer = {
        "inputMode": "text",
        "text": pronunciation["publicContent"]["targetText"],
        "idempotencyKey": "same-attempt-key",
    }
    with ThreadPoolExecutor(max_workers=4) as pool:
        evaluated = list(
            pool.map(
                lambda _: client.post(f"/api/v1/tasks/{pronunciation['id']}/attempts", json=answer),
                range(4),
            )
        )
    assert all(r.status_code == 200 for r in evaluated), [r.text for r in evaluated]
    assert len({r.json()["attempt"]["id"] for r in evaluated}) == 1
    assert (
        client.post(
            f"/api/v1/tasks/{pronunciation['id']}/attempts", json=answer | {"text": "different"}
        ).status_code
        == 409
    )
    with engine.connect() as c:
        assert (
            c.execute(
                select(func.count())
                .select_from(task_attempts)
                .where(task_attempts.c.session_task_id == UUID(pronunciation["id"]))
            ).scalar_one()
            == 1
        )
        events = (
            c.execute(
                select(vocabulary_encounters).where(vocabulary_encounters.c.session_id == UUID(sid))
            )
            .mappings()
            .all()
        )
        assert len(events) == 2
        progress = (
            c.execute(
                select(user_vocabulary_progress).where(
                    user_vocabulary_progress.c.user_id == owner.id
                )
            )
            .mappings()
            .one()
        )
        assert progress["exposure_count"] == 2 and progress["correct_attempt_count"] == 1
    for task in tasks[2:]:
        skip = f"/api/v1/tasks/{task['id']}/skip"
        assert client.post(skip, json={}).status_code == 200
        assert client.post(skip, json={}).status_code == 200
    assert client.get("/api/v1/me/progress").json()["xp"] == 10
    assert client.post(endpoint + "/complete").status_code == 200
    assert client.post(endpoint + "/complete").status_code == 200
    summary = client.get(endpoint + "/summary").json()
    assert summary["xpEarned"] == 10
    assert summary["ispyCorrectCount"] == summary["ispyAttemptCount"] == 0
    assert summary["progress"]["completedTaskCount"] == 2
    assert summary["progress"]["skippedTaskCount"] == 6
    assert len(summary["learnedVocabularyIds"]) == 1
    assert client.post(f"/api/v1/tasks/{intro}/skip", json={}).status_code == 409
    with TestClient(create_app()) as restarted:
        assert restarted.get(endpoint).json()["progress"] == summary["progress"]
    assert PostgresWorkflowRepository(engine, uuid4()).active(profile.id) is None


def test_skip_all_adds_no_learning_credit(database):
    _, _, profile, client = database
    sid = create_run(client, profile)["session"]["id"]
    detail = analyze(client, sid)
    for task in detail["tasks"]:
        assert client.post(f"/api/v1/tasks/{task['id']}/skip", json={}).status_code == 200
    assert client.post(f"/api/v1/sessions/{sid}/complete").status_code == 200
    assert client.get("/api/v1/me/progress").json()["xp"] == 0
    assert client.get("/api/v1/me/vocabulary").json()["items"] == []
    summary = client.get(f"/api/v1/sessions/{sid}/summary").json()
    assert summary["xpEarned"] == 0
    assert summary["ispyCorrectCount"] == summary["ispyAttemptCount"] == 0


def test_task_updates_roll_back_with_encounter_failure(database, monkeypatch):
    engine, owner, profile, client = database
    sid = create_run(client, profile)["session"]["id"]
    detail = analyze(client, sid)

    def fail(*args, **kwargs):
        raise RuntimeError("Simulated progress write failure")

    with monkeypatch.context() as patcher:
        patcher.setattr(PostgresWorkflowRepository, "_encounter", fail)
        with pytest.raises(RuntimeError):
            client.post(
                f"/api/v1/tasks/{detail['tasks'][1]['id']}/attempts",
                json={"inputMode": "text", "text": "test"},
            )
    with engine.connect() as c:
        assert (
            c.execute(
                select(func.count())
                .select_from(task_attempts)
                .where(task_attempts.c.session_task_id == UUID(detail["tasks"][1]["id"]))
            ).scalar_one()
            == 0
        )
    assert client.get(f"/api/v1/sessions/{sid}").json()["tasks"][1]["status"] == "pending"


def upload_asset(engine, owner):
    asset = MediaAsset(
        owner_user_id=owner.id,
        source="userUpload",
        media_type="image",
        storage_key=f"users/{owner.id}/images/{uuid4()}.jpg",
        mime_type="image/jpeg",
    )
    with engine.begin() as c:
        c.execute(insert(media_assets).values(**asset.model_dump(by_alias=False)))
    return asset.id


def create_with_asset(client, profile, asset_id, key):
    return client.post(
        "/api/v1/sessions",
        json={
            "languageProfileId": str(profile.id),
            "mediaAssetId": str(asset_id),
            "idempotencyKey": key,
        },
    )


def age_session(engine, session_id, status, updated_at):
    # The sessions_updated_at trigger overwrites updated_at on every UPDATE, so
    # it must be disabled to backdate a row for the timeout rules.
    with engine.begin() as c:
        c.execute(text("ALTER TABLE sessions DISABLE TRIGGER sessions_updated_at"))
        c.execute(
            update(sessions)
            .where(sessions.c.id == session_id)
            .values(status=status, updated_at=updated_at)
        )
        c.execute(text("ALTER TABLE sessions ENABLE TRIGGER sessions_updated_at"))


def test_active_session_replacement_and_owner_scope(database, monkeypatch):
    engine, owner, profile, client = database
    first = create_run(client, profile)["session"]["id"]
    # The same image under a different key continues the open run.
    continued = create_run(client, profile, "replacement-key")
    assert continued["session"]["id"] == first
    assert client.get(f"/api/v1/sessions/{first}").json()["session"]["status"] == "created"
    # A different image conflicts while a session is still active.
    asset = upload_asset(engine, owner)
    conflict = create_with_asset(client, profile, asset, "other-asset-key")
    assert conflict.status_code == 409
    detail = conflict.json()["detail"]
    assert detail["code"] == "active_session_exists"
    assert detail["activeSessionId"] == first
    with engine.connect() as c:
        ids = c.execute(select(sessions.c.id).where(sessions.c.user_id == owner.id)).scalars().all()
    assert ids == [UUID(first)]
    # Discarding the open run frees the profile for the new image.
    assert client.post(f"/api/v1/sessions/{first}/abandon").status_code == 200
    assert client.post(f"/api/v1/sessions/{first}/analyze").status_code == 409
    created = create_with_asset(client, profile, asset, "other-asset-key-2")
    assert created.status_code == 202, created.text
    replacement = created.json()["session"]["id"]
    assert client.get("/api/v1/sessions/active").json()["session"]["id"] == replacement
    with pytest.raises(IntegrityError), engine.begin() as c:
        c.execute(
            update(sessions).where(sessions.c.id == UUID(replacement)).values(status="completed")
        )
    monkeypatch.setenv("DEMO_USER_ID", str(uuid4()))
    assert client.get(f"/api/v1/sessions/{replacement}").status_code == 404


def test_reap_expires_stale_sessions_but_keeps_real_work(database):
    engine, owner, profile, client = database
    # A crashed analysis older than 15 minutes is failed, not blocking.
    first = create_run(client, profile)["session"]["id"]
    age_session(engine, UUID(first), "analyzingScene", utc_now() - timedelta(minutes=30))
    asset = upload_asset(engine, owner)
    created = create_with_asset(client, profile, asset, "after-analysis-timeout")
    assert created.status_code == 202, created.text
    second = created.json()["session"]["id"]
    assert second != first
    with engine.connect() as c:
        old = c.execute(select(sessions).where(sessions.c.id == UUID(first))).mappings().one()
    assert old["status"] == "failed" and old["failure_code"] == "analysis_timeout"
    # A pre-review session older than 24 hours is abandoned; no work is lost.
    age_session(engine, UUID(second), "created", utc_now() - timedelta(hours=25))
    asset2 = upload_asset(engine, owner)
    created2 = create_with_asset(client, profile, asset2, "after-stale-created")
    assert created2.status_code == 202, created2.text
    third = created2.json()["session"]["id"]
    with engine.connect() as c:
        old = c.execute(select(sessions).where(sessions.c.id == UUID(second))).mappings().one()
    assert old["status"] == "abandoned" and old["abandoned_at"] is not None
    # An in-progress session with recorded attempts is never reaped.
    detail = analyze(client, third)
    attempt = TaskAttempt(
        session_task_id=UUID(detail["tasks"][0]["id"]),
        attempt_number=1,
        input_mode="text",
        response_payload={"text": "hola"},
    )
    with engine.begin() as c:
        c.execute(insert(task_attempts).values(**entity_values(attempt)))
    age_session(engine, UUID(third), "inProgress", utc_now() - timedelta(days=8))
    asset3 = upload_asset(engine, owner)
    conflict = create_with_asset(client, profile, asset3, "still-blocked")
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["activeSessionId"] == third


def test_all_task_kinds_complete_with_server_evaluation(database):
    engine, owner, profile, client = database
    sid = create_run(client, profile)["session"]["id"]
    detail = analyze(client, sid)
    for task in detail["tasks"]:
        endpoint = f"/api/v1/tasks/{task['id']}"
        assert client.post(endpoint + "/start").status_code == 200
        content = task["publicContent"]
        kind = task["kind"]
        if kind in {"vocabularyIntroduction", "grammarExplanation", "syntaxExplanation"}:
            result = client.post(endpoint + "/complete")
        else:
            assert client.post(endpoint + "/complete").status_code == 409
            if kind == "ispyRound":
                with engine.connect() as c:
                    key = c.execute(
                        select(session_tasks.c.answer_key).where(
                            session_tasks.c.id == UUID(task["id"])
                        )
                    ).scalar_one()
                answer = {
                    "inputMode": "objectSelection",
                    "sceneObjectId": key["correctSceneObjectId"],
                }
            else:
                value = (
                    content.get("targetText") or content.get("sourceText") or "A sample reflection."
                )
                if kind == "grammarPractice":
                    value = "A deliberately incorrect answer"
                answer = {"inputMode": "text", "text": value}
            result = client.post(
                endpoint + "/attempts", json=answer | {"idempotencyKey": "evaluated-once-key"}
            )
        assert result.status_code == 200, result.text
        assert "answerKey" not in result.text
        if kind == "grammarPractice":
            assert result.json()["attempt"]["isCorrect"] is False
    assert client.post(f"/api/v1/sessions/{sid}/complete").status_code == 200
    assert client.get("/api/v1/me/progress").json()["xp"] == 30
    summary = client.get(f"/api/v1/sessions/{sid}/summary").json()
    assert summary["xpEarned"] == 30
    assert summary["ispyCorrectCount"] == summary["ispyAttemptCount"] == 1
    with engine.connect() as c:
        progress = (
            c.execute(
                select(user_vocabulary_progress).where(
                    user_vocabulary_progress.c.user_id == owner.id
                )
            )
            .mappings()
            .one()
        )
        assert progress["exposure_count"] == 6
        assert progress["correct_attempt_count"] == 3
    # Planning another session reuses vocabulary and does not credit exposure.
    other = create_run(client, profile, "another-session-key")
    again = analyze(client, other["session"]["id"])
    assert {v["id"] for v in again["vocabulary"]} == {v["id"] for v in detail["vocabulary"]}
    assert client.get("/api/v1/me/progress").json()["xp"] == 30


def test_other_user_cannot_access_sessions_or_tasks(database, monkeypatch):
    engine, owner, profile, client = database
    sid = create_run(client, profile)["session"]["id"]
    detail = analyze(client, sid)
    stranger = User(display_name="Other learner", auth_provider_id=f"stranger-{uuid4()}")
    with engine.begin() as c:
        c.execute(insert(users).values(**stranger.model_dump(by_alias=False)))
    try:
        PostgresLanguageProfileRepository(engine).create(
            LanguageProfile(
                user_id=stranger.id,
                source_language_code="en",
                target_language_code="es",
                proficiency_level="A1",
            )
        )
        monkeypatch.setenv("DEMO_USER_ID", str(stranger.id))
        assert client.get(f"/api/v1/sessions/{sid}").status_code == 404
        task = detail["tasks"][0]["id"]
        assert client.get(f"/api/v1/tasks/{task}").status_code == 404
        assert client.post(f"/api/v1/tasks/{task}/complete").status_code == 404
        assert client.post(f"/api/v1/sessions/{sid}/analyze").status_code == 404
    finally:
        with engine.begin() as c:
            c.execute(delete(users).where(users.c.id == stranger.id))


def test_review_rejects_adds_and_rebuilds_without_duplicate_objects(database):
    _, _, profile, client = database
    run = create_run(client, profile, "review-session-key")
    sid = run["session"]["id"]
    detail = analyze(client, sid, confirm=False)
    kept = detail["sceneObjects"][0]["id"]
    payload = {
        "acceptedObjectIds": [kept],
        "addedObjects": [
            {
                "id": str(uuid4()),
                "label": detail["sceneObjects"][1]["detectedLabel"],
                "x": 0.3,
                "y": 0.4,
            }
        ],
    }
    response = client.put(f"/api/v1/sessions/{sid}/review", json=payload)
    assert response.status_code == 200, response.text
    saved = response.json()
    selected = [obj for obj in saved["sceneObjects"] if obj["selectionStatus"] != "rejected"]
    assert len(selected) == 2
    assert any(
        obj["detectedLabel"] == detail["sceneObjects"][1]["detectedLabel"] for obj in selected
    )
    assert all(task["sceneObjectId"] in {obj["id"] for obj in selected} for task in saved["tasks"])
    introductions = [task for task in saved["tasks"] if task["kind"] == "vocabularyIntroduction"]
    assert len(introductions) == 2
    retry = client.put(f"/api/v1/sessions/{sid}/review", json=payload)
    assert retry.status_code == 200, retry.text
    assert len(retry.json()["sceneObjects"]) == len(saved["sceneObjects"])
    task_id = introductions[0]["id"]
    assert client.post(f"/api/v1/tasks/{task_id}/complete", json={}).status_code == 200
    assert client.put(f"/api/v1/sessions/{sid}/review", json=payload).status_code == 409
    persisted = client.get(f"/api/v1/sessions/{sid}").json()
    assert (
        next(task for task in persisted["tasks"] if task["id"] == task_id)["status"] == "completed"
    )
