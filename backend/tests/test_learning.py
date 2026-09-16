import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_learning_repository
from app.config import DEFAULT_DEMO_USER_ID, DEMO_USERS_PATH
from app.main import create_app
from app.repositories.implementations.json.learning import JsonLearningRepository
from app.repositories.implementations.json.users import JsonUserRepository
from app.repositories.learning import LearningStorageError
from app.schemas.base import CursorPage
from app.schemas.progress import ProgressResponse
from app.schemas.vocabulary import DailyVocabularyItem
from app.services.learning import InvalidCursorError, LearningService
from app.services.users import UserService

USER_ID = UUID(DEFAULT_DEMO_USER_ID)


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    for filename in ["progress.json", "vocabulary.json"]:
        (tmp_path / filename).write_bytes((DEMO_USERS_PATH.parent / filename).read_bytes())
    return tmp_path


@pytest.fixture
def client(data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DEMO_USER_ID", DEFAULT_DEMO_USER_ID)
    app = create_app()
    app.dependency_overrides[get_learning_repository] = lambda: JsonLearningRepository(data_dir)
    return TestClient(app)


def test_repository_loads_migrated_data(data_dir: Path) -> None:
    repository = JsonLearningRepository(data_dir)
    progress = repository.get_progress(USER_ID)
    assert progress is not None
    assert progress.xp == 1280
    assert len(progress.scenarios) == 3
    assert len(progress.leaderboard) == 5
    words = repository.list_vocabulary(USER_ID)
    assert len(words) == 12
    assert words[0].vocabulary.display_text == "la calle"
    assert words[0].topic == "City"
    assert words[1].vocabulary.display_text == "el autobús"
    assert repository.list_vocabulary(uuid4()) == []
    assert repository.get_progress(uuid4()) is None


def test_repository_filters_other_users(data_dir: Path) -> None:
    path = data_dir / "vocabulary.json"
    words = json.loads(path.read_text(encoding="utf-8"))
    words[0]["progress"]["userId"] = str(uuid4())
    path.write_text(json.dumps(words), encoding="utf-8")
    assert len(JsonLearningRepository(data_dir).list_vocabulary(USER_ID)) == 11


def test_service_paginates_and_rejects_bad_cursor(data_dir: Path) -> None:
    users = UserService(JsonUserRepository(DEMO_USERS_PATH), USER_ID)
    service = LearningService(JsonLearningRepository(data_dir), users)
    first = service.list_vocabulary(None, 5)
    second = service.list_vocabulary(first.next_cursor, 5)
    third = service.list_vocabulary(second.next_cursor, 5)
    ids = [item.vocabulary.id for page in [first, second, third] for item in page.items]
    assert len(ids) == len(set(ids)) == 12
    assert third.next_cursor is None
    with pytest.raises(InvalidCursorError):
        service.list_vocabulary("bad", 5)
    board = service.get_progress().leaderboard
    assert next(row for row in board if row.is_you).name == users.get_current_user().display_name
    assert [row.rank for row in board] == [1, 2, 3, 4, 5]


def test_progress_response(client: TestClient) -> None:
    response = client.get("/api/v1/me/progress")
    assert response.status_code == 200
    body = response.json()
    assert "userId" not in body
    assert ProgressResponse.model_validate(body).xp == 1280


def test_vocabulary_response_and_pagination(client: TestClient) -> None:
    response = client.get("/api/v1/me/vocabulary?limit=10")
    assert response.status_code == 200
    page = CursorPage[DailyVocabularyItem].model_validate(response.json())
    assert len(page.items) == 10
    final = client.get("/api/v1/me/vocabulary", params={"cursor": page.next_cursor})
    assert len(final.json()["items"]) == 2
    assert final.json()["nextCursor"] is None
    assert client.get("/api/v1/me/vocabulary?cursor=invalid").status_code == 400
    assert client.get("/api/v1/me/vocabulary?limit=0").status_code == 422
    assert client.get("/api/v1/me/vocabulary?limit=101").status_code == 422


@pytest.mark.parametrize("endpoint", ["progress", "vocabulary"])
def test_missing_user(client: TestClient, monkeypatch: pytest.MonkeyPatch, endpoint: str) -> None:
    monkeypatch.setenv("DEMO_USER_ID", str(uuid4()))
    response = client.get(f"/api/v1/me/{endpoint}")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "user_not_found"


def test_empty_data(client: TestClient, data_dir: Path) -> None:
    for name in ["vocabulary", "progress"]:
        (data_dir / f"{name}.json").write_text("[]", encoding="utf-8")
    assert client.get("/api/v1/me/vocabulary").json() == {"items": [], "nextCursor": None}
    assert client.get("/api/v1/me/progress").status_code == 404


@pytest.mark.parametrize("endpoint", ["progress", "vocabulary"])
@pytest.mark.parametrize("contents", ["invalid json", '[{"invalid": true}]'])
def test_invalid_storage_is_controlled(
    client: TestClient, data_dir: Path, endpoint: str, contents: str
) -> None:
    (data_dir / f"{endpoint}.json").write_text(contents, encoding="utf-8")
    response = client.get(f"/api/v1/me/{endpoint}", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "learning_storage_error"
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_missing_file_is_controlled(tmp_path: Path) -> None:
    with pytest.raises(LearningStorageError):
        JsonLearningRepository(tmp_path).list_vocabulary(USER_ID)


def test_other_vocabulary_routes_remain_unimplemented(client: TestClient) -> None:
    assert client.get("/api/v1/me/vocabulary/daily").status_code == 501
    assert client.get(f"/api/v1/me/vocabulary/{uuid4()}").status_code == 501
