import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_language_profile_repository, get_user_repository
from app.config import DEFAULT_DEMO_USER_ID, DEMO_USERS_PATH
from app.main import create_app
from app.repositories.implementations.json import store
from app.repositories.implementations.json.language_profiles import JsonLanguageProfileRepository
from app.repositories.implementations.json.users import JsonUserRepository
from app.schemas.users import CreateLanguageProfileRequest, UpdateLanguageProfileRequest
from app.services.language_profiles import LanguageProfileService
from app.services.users import UserService

USER_ID = UUID(DEFAULT_DEMO_USER_ID)


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    for name in ["users.json", "language_profiles.json"]:
        (tmp_path / name).write_bytes((DEMO_USERS_PATH.parent / name).read_bytes())
    path = tmp_path / "language_profiles.json"
    spanish = next(
        row
        for row in json.loads(path.read_text(encoding="utf-8"))
        if row["id"] == "22222222-2222-4222-8222-222222222222"
    )
    spanish["isActive"] = True
    path.write_text(json.dumps([spanish]), encoding="utf-8")
    return tmp_path


@pytest.fixture
def client(data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DEMO_USER_ID", DEFAULT_DEMO_USER_ID)
    app = create_app()
    app.dependency_overrides[get_user_repository] = lambda: JsonUserRepository(
        data_dir / "users.json"
    )
    app.dependency_overrides[get_language_profile_repository] = lambda: (
        JsonLanguageProfileRepository(data_dir / "language_profiles.json")
    )
    return TestClient(app)


def create(client: TestClient, language: str = "fr"):
    return client.post(
        "/api/v1/me/language-profiles",
        json={
            "sourceLanguageCode": "en",
            "targetLanguageCode": language,
            "proficiencyLevel": "A1",
            "dailyGoalMinutes": 20,
        },
    )


def test_language_switch_filters_all_content_and_survives_reload(
    client: TestClient, data_dir: Path
):
    spanish = client.get("/api/v1/me/language-profiles").json()[0]
    assert len(client.get("/api/v1/preloaded-scenes").json()) == 6
    response = create(client)
    assert response.status_code == 201
    french = response.json()
    assert french["isActive"]
    assert client.get("/api/v1/preloaded-scenes").json() == []
    assert client.get("/api/v1/me/vocabulary").json()["items"] == []
    assert client.get("/api/v1/me/progress").json() == {"xp": 0, "scenarios": [], "leaderboard": []}
    assert client.get("/api/v1/preloaded-scenes/calle-mayor").status_code == 404
    reloaded = JsonLanguageProfileRepository(data_dir / "language_profiles.json").list_for_user(
        USER_ID
    )
    assert [row.target_language_code for row in reloaded if row.is_active] == ["fr"]
    response = client.patch(
        f"/api/v1/me/language-profiles/{spanish['id']}", json={"isActive": True}
    )
    assert response.status_code == 200
    assert len(client.get("/api/v1/preloaded-scenes").json()) == 6
    assert len(client.get("/api/v1/me/vocabulary").json()["items"]) == 12
    assert client.get("/api/v1/me/progress").json()["xp"] == 1280
    rows = client.get("/api/v1/me/language-profiles").json()
    assert sum(row["isActive"] for row in rows) == 1
    assert next(row for row in rows if row["id"] == french["id"])["dailyGoalMinutes"] == 20


def test_user_and_language_preferences_persist(client: TestClient, data_dir: Path):
    before = client.get("/api/v1/me").json()
    response = client.patch(
        "/api/v1/me",
        json={
            "displayName": "New Name",
            "learningGoal": "Travel",
            "microphoneEnabled": False,
            "cameraEnabled": False,
            "onboardingCompleted": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["id"] == before["id"]
    assert response.json()["createdAt"] == before["createdAt"]
    user = JsonUserRepository(data_dir / "users.json").get_by_id(USER_ID)
    assert user.display_name == "New Name" and user.learning_goal == "Travel"
    assert not user.microphone_enabled and not user.camera_enabled
    assert client.get("/api/v1/me/progress").json()["leaderboard"][1]["name"] == "New Name"
    profile = client.get("/api/v1/me/language-profiles").json()[0]
    url = f"/api/v1/me/language-profiles/{profile['id']}"
    assert (
        client.patch(url, json={"dailyGoalMinutes": 5, "proficiencyLevel": "B1"}).status_code == 200
    )
    assert client.get("/api/v1/me/language-profiles").json()[0]["dailyGoalMinutes"] == 5
    assert client.patch(url, json={"dailyGoalMinutes": None}).json()["dailyGoalMinutes"] is None
    assert client.patch(url, json={"dailyGoalMinutes": 0}).status_code == 422
    assert client.patch("/api/v1/me", json={"displayName": " "}).status_code == 422


def test_other_user_profiles_are_isolated(client: TestClient, data_dir: Path):
    path = data_dir / "language_profiles.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    other = dict(rows[0], id=str(uuid4()), userId=str(uuid4()))
    rows.append(other)
    path.write_text(json.dumps(rows), encoding="utf-8")
    assert len(client.get("/api/v1/me/language-profiles").json()) == 1
    assert (
        client.patch(
            f"/api/v1/me/language-profiles/{other['id']}", json={"isActive": False}
        ).status_code
        == 404
    )
    assert create(client).status_code == 201
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert next(row for row in saved if row["id"] == other["id"])["isActive"]


def test_validation_duplicates_no_active_and_cors(client: TestClient):
    assert create(client, "es").status_code == 409
    assert create(client, "en").status_code == 422
    profile = client.get("/api/v1/me/language-profiles").json()[0]
    assert (
        client.patch(
            f"/api/v1/me/language-profiles/{profile['id']}", json={"isActive": False}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/preloaded-scenes").status_code == 409
    for method in ["POST", "PATCH"]:
        response = client.options(
            "/api/v1/me/language-profiles",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_invalid_storage_and_failed_write_preserve_file(
    client: TestClient, data_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    path = data_dir / "language_profiles.json"
    original = path.read_bytes()

    def fail_replace(*args):
        raise OSError("disk unavailable")

    monkeypatch.setattr(store.os, "replace", fail_replace)
    assert create(client).status_code == 500
    assert path.read_bytes() == original
    path.write_text("invalid", encoding="utf-8")
    assert client.get("/api/v1/me/language-profiles").status_code == 500


def test_service_concurrent_activation(data_dir: Path):
    users = UserService(JsonUserRepository(data_dir / "users.json"), USER_ID)
    service = LanguageProfileService(
        JsonLanguageProfileRepository(data_dir / "language_profiles.json"), users
    )
    profile = service.create(
        CreateLanguageProfileRequest(
            source_language_code="en", target_language_code="fr", proficiency_level="A1"
        )
    )
    ids = [row.id for row in service.list_profiles()]
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(
            pool.map(
                lambda id: service.update(id, UpdateLanguageProfileRequest(is_active=True)), ids
            )
        )
    assert sum(row.is_active for row in service.list_profiles()) == 1
    assert profile.target_language_code == "fr"
