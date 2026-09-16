import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import dependencies as deps
from app.config import DEFAULT_DEMO_USER_ID, DEMO_USERS_PATH
from app.main import create_app
from app.repositories.implementations.json import store
from app.repositories.implementations.json.journals import JsonJournalRepository
from app.repositories.implementations.json.language_profiles import JsonLanguageProfileRepository
from app.repositories.implementations.json.learning import JsonLearningRepository
from app.repositories.implementations.json.practice import JsonPracticeRepository
from app.repositories.implementations.json.users import JsonUserRepository
from app.repositories.practice import PracticeStorageError

PROFILE = "22222222-2222-4222-8222-222222222222"


@pytest.fixture
def data_dir(tmp_path: Path):
    for name in ["users", "language_profiles", "progress", "vocabulary"]:
        (tmp_path / f"{name}.json").write_bytes(
            (DEMO_USERS_PATH.parent / f"{name}.json").read_bytes()
        )
    path = tmp_path / "language_profiles.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        row["isActive"] = row["id"] == PROFILE
    path.write_text(json.dumps(rows), encoding="utf-8")
    (tmp_path / "journals.json").write_text("[]", encoding="utf-8")
    return tmp_path


def make_client(data_dir: Path):
    app = create_app()
    app.dependency_overrides.update(
        {
            deps.get_user_repository: lambda: JsonUserRepository(data_dir / "users.json"),
            deps.get_language_profile_repository: lambda: JsonLanguageProfileRepository(
                data_dir / "language_profiles.json"
            ),
            deps.get_learning_repository: lambda: JsonLearningRepository(data_dir),
            deps.get_practice_repository: lambda: JsonPracticeRepository(
                data_dir / "progress.json"
            ),
            deps.get_journal_repository: lambda: JsonJournalRepository(data_dir / "journals.json"),
        }
    )
    return TestClient(app)


@pytest.fixture
def client(data_dir, monkeypatch):
    monkeypatch.setenv("DEMO_USER_ID", DEFAULT_DEMO_USER_ID)
    return make_client(data_dir)


def new_session(client, key="test-run"):
    scene = client.get("/api/v1/preloaded-scenes/calle-mayor").json()
    response = client.post(
        "/api/v1/sessions",
        json={
            "languageProfileId": PROFILE,
            "mediaAssetId": scene["mediaAsset"]["id"],
            "idempotencyKey": key,
        },
    )
    assert response.status_code == 202, response.text
    return response.json()["session"]["id"], scene


def event(client, session_id, **body):
    return client.post(f"/api/v1/sessions/{session_id}/demo-events", json=body)


def test_xp_survives_restart_and_retries(client, data_dir):
    before = client.get("/api/v1/me/progress").json()["xp"]
    session_id, _ = new_session(client)
    assert new_session(client)[0] == session_id
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda _: event(client, session_id, kind="analysis"), range(8)))
    assert all(response.status_code == 200 for response in responses)
    fresh = make_client(data_dir)
    assert fresh.get("/api/v1/me/progress").json()["xp"] == before + 12
    run = fresh.get(f"/api/v1/sessions/{session_id}").json()
    assert run["demoState"]["sessionXp"] == 12
    assert fresh.get("/api/v1/sessions/active").json()["session"]["id"] == session_id
    assert JsonPracticeRepository(data_dir / "progress.json").read()[0].xp == before + 12


def test_complete_session_and_server_scoring(client, data_dir):
    before = client.get("/api/v1/me/progress").json()["xp"]
    sid, scene = new_session(client)
    assert client.post(f"/api/v1/sessions/{sid}/complete").status_code == 409
    assert event(client, sid, kind="analysis", xp=9999).status_code == 422
    assert event(client, sid, kind="task", itemId="unknown").status_code == 409
    assert event(client, sid, kind="analysis").status_code == 200
    expected = 12
    for task in scene["tasks"]:
        assert event(client, sid, kind="task", itemId=task["id"]).status_code == 200
        expected += task["xp"]
    for round in scene["rounds"]:
        assert (
            event(client, sid, kind="round", itemId=round["id"], answerId="bad").status_code == 409
        )
        assert (
            event(
                client, sid, kind="round", itemId=round["id"], answerId=round["answerId"]
            ).status_code
            == 200
        )
        expected += 5
    for prompt in scene["prompts"]:
        assert (
            event(client, sid, kind="clue", itemId=prompt["id"], text="A clue").status_code == 200
        )
        expected += 2
    for _ in range(2):
        assert client.post(f"/api/v1/sessions/{sid}/complete").status_code == 200
    assert event(client, sid, kind="analysis").status_code == 200
    fresh = make_client(data_dir)
    assert fresh.get("/api/v1/me/progress").json()["xp"] == before + expected
    run = fresh.get(f"/api/v1/sessions/{sid}").json()
    assert run["session"]["status"] == "completed"
    assert run["demoState"]["answers"]
    assert run["demoState"]["clues"]
    assert new_session(fresh, "intentional-replay")[0] != sid


def test_failed_write_and_invalid_storage(client, data_dir, monkeypatch):
    sid, _ = new_session(client)
    path = data_dir / "progress.json"
    before = path.read_bytes()

    def fail(*args):
        raise OSError("disk unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(store.os, "replace", fail)
        assert event(client, sid, kind="analysis").status_code == 500
    assert path.read_bytes() == before
    assert event(client, sid, kind="analysis").status_code == 200
    path.write_text("invalid", encoding="utf-8")
    with pytest.raises(PracticeStorageError):
        JsonPracticeRepository(path).read()
    assert client.get(f"/api/v1/sessions/{sid}").status_code == 500


def test_session_isolation(client, data_dir):
    sid, _ = new_session(client)
    path = data_dir / "progress.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    rows[0]["userId"] = str(uuid4())
    path.write_text(json.dumps(rows), encoding="utf-8")
    assert client.get(f"/api/v1/sessions/{sid}").status_code == 404
    assert event(client, sid, kind="analysis").status_code == 404
    assert client.get("/api/v1/sessions/active").json() is None


def test_journal_save_edit_reload_and_idempotency(client, data_dir):
    payload = {
        "languageProfileId": PROFILE,
        "title": "My day",
        "content": "Hola mundo",
        "art": "street",
        "selectedWords": ["hola"],
    }
    first = client.put("/api/v1/journal/today", json=payload)
    assert first.status_code == 200, first.text
    jid = first.json()["id"]
    assert client.put("/api/v1/journal/today", json=payload).json()["id"] == jid
    assert client.get("/api/v1/journal/today/context").json()["canCreate"] is False
    assert len(client.get(f"/api/v1/journals/{jid}").json()["revisions"]) == 1
    assert (
        client.patch(f"/api/v1/journals/{jid}", json={"content": "Hola otra vez"}).status_code
        == 200
    )
    fresh = make_client(data_dir)
    entry = fresh.get(f"/api/v1/journals/{jid}").json()
    assert entry["revisions"][-1]["content"] == "Hola otra vez"
    assert len(entry["revisions"]) == 2
    assert len(fresh.get("/api/v1/journals").json()) == 1
    assert JsonJournalRepository(data_dir / "journals.json").read()[0].journal.id == UUID(jid)


def test_journal_missing_other_user_and_invalid_storage(client, data_dir):
    missing = uuid4()
    assert client.get(f"/api/v1/journals/{missing}").status_code == 404
    assert client.patch(f"/api/v1/journals/{missing}", json={"title": "X"}).status_code == 404
    payload = {"languageProfileId": PROFILE, "content": "Hello"}
    jid = client.put("/api/v1/journal/today", json=payload).json()["id"]
    path = data_dir / "journals.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    rows[0]["journal"]["userId"] = str(uuid4())
    path.write_text(json.dumps(rows), encoding="utf-8")
    assert client.get("/api/v1/journals").json() == []
    assert client.get(f"/api/v1/journals/{jid}").status_code == 404
    path.write_text("invalid", encoding="utf-8")
    assert client.get("/api/v1/journals").status_code == 500


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH"])
def test_cors_writes(client, method):
    response = client.options(
        "/api/v1/journal/today",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
