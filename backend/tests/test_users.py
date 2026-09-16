import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_user_repository
from app.config import DEFAULT_DEMO_USER_ID, DEMO_USERS_PATH
from app.main import create_app
from app.repositories.implementations.json.users import JsonUserRepository
from app.repositories.users import UserRepositoryError
from app.schemas.users import User
from app.services.users import UserNotFoundError, UserService


@pytest.fixture
def user() -> User:
    return User.model_validate(json.loads(DEMO_USERS_PATH.read_text(encoding="utf-8"))[0])


def test_json_repository_reads_existing_user(user: User) -> None:
    assert JsonUserRepository(DEMO_USERS_PATH).get_by_id(user.id) == user


def test_json_repository_missing_user() -> None:
    assert JsonUserRepository(DEMO_USERS_PATH).get_by_id(uuid4()) is None


@pytest.mark.parametrize("contents", ["{broken", "{}", '[{"displayName": "Alex"}]', "\xff"])
def test_json_repository_invalid_data(tmp_path: Path, contents: str) -> None:
    path = tmp_path / "users.json"
    path.write_bytes(contents.encode("latin-1"))
    with pytest.raises(UserRepositoryError):
        JsonUserRepository(path).get_by_id(UUID(DEFAULT_DEMO_USER_ID))


def test_json_repository_unreadable_file(tmp_path: Path) -> None:
    with pytest.raises(UserRepositoryError):
        JsonUserRepository(tmp_path / "missing.json").get_by_id(uuid4())


def test_service_returns_repository_user(user: User) -> None:
    class Repository:
        def get_by_id(self, user_id: UUID) -> User | None:
            assert user_id == user.id
            return user

    assert UserService(Repository(), user.id).get_current_user() == user


def test_service_missing_user() -> None:
    class Repository:
        def get_by_id(self, user_id: UUID) -> User | None:
            return None

    with pytest.raises(UserNotFoundError):
        UserService(Repository(), uuid4()).get_current_user()


def test_me_reads_json_and_serializes_contract(user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_USER_ID", str(user.id))
    response = TestClient(create_app()).get("/api/v1/me")
    assert response.status_code == 200
    assert response.json() == user.model_dump(mode="json", by_alias=True)


def test_me_missing_configured_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_USER_ID", str(uuid4()))
    response = TestClient(create_app()).get("/api/v1/me")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "user_not_found"


@pytest.mark.parametrize("contents", ["not json", '[{"unexpected": true}]'])
def test_me_invalid_storage_is_controlled(tmp_path: Path, contents: str) -> None:
    path = tmp_path / "users.json"
    path.write_text(contents, encoding="utf-8")
    app = create_app()
    app.dependency_overrides[get_user_repository] = lambda: JsonUserRepository(path)
    response = TestClient(app).get("/api/v1/me")
    assert response.status_code == 500
    assert response.json() == {
        "detail": {"code": "user_storage_error", "message": "Unable to load demo user data."}
    }


def test_cors_environment_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173, https://example.com")
    client = TestClient(create_app())
    for origin in ["http://localhost:5173", "https://example.com"]:
        response = client.get("/api/v1/me", headers={"Origin": origin})
        assert response.headers["access-control-allow-origin"] == origin
        preflight = client.options(
            "/api/v1/me",
            headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
        )
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-origin"] == origin
    response = client.get("/api/v1/me", headers={"Origin": "https://unlisted.example"})
    assert "access-control-allow-origin" not in response.headers
