import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_scene_repository
from app.config import DEMO_USERS_PATH
from app.main import create_app
from app.repositories.implementations.json.scenes import JsonSceneRepository
from app.repositories.scenes import SceneStorageError
from app.schemas.media import PreloadedScene
from app.schemas.scenes import PreloadedSceneDetail
from app.services.scenes import SceneNotFoundError, SceneService


@pytest.fixture
def path(tmp_path: Path) -> Path:
    path = tmp_path / "scenes.json"
    path.write_bytes((DEMO_USERS_PATH.parent / "scenes.json").read_bytes())
    return path


@pytest.fixture
def client(path: Path) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_scene_repository] = lambda: JsonSceneRepository(path)
    return TestClient(app)


def test_migrated_scenes_and_service(path: Path) -> None:
    repository = JsonSceneRepository(path)
    scenes = repository.list_scenes()
    assert {row.scene_id for row in scenes} == {
        "calle-mayor",
        "cafe-plaza",
        "mercado-central",
        "el-parque",
        "mi-cuarto",
        "la-cocina",
    }
    service = SceneService(repository)
    summaries = service.list_scenes()
    assert all(type(row) is PreloadedScene for row in summaries)
    assert service.get_scene("calle-mayor").items[0].word == "la calle"
    with pytest.raises(SceneNotFoundError):
        service.get_scene("unknown")


def test_catalog_and_detail(client: TestClient) -> None:
    response = client.get("/api/v1/preloaded-scenes", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    for row in response.json():
        PreloadedScene.model_validate(row)
        assert "items" not in row
        assert "rounds" not in row
        detail = client.get(f"/api/v1/preloaded-scenes/{row['sceneId']}")
        assert detail.status_code == 200
        scene = PreloadedSceneDetail.model_validate(detail.json())
        assert scene.scene_id == row["sceneId"]
        assert scene.items and scene.tasks and scene.rounds and scene.prompts
    assert client.get("/api/v1/preloaded-scenes/unknown").status_code == 404


def test_empty_catalog(client: TestClient, path: Path) -> None:
    path.write_text("[]", encoding="utf-8")
    assert client.get("/api/v1/preloaded-scenes").json() == []
    assert client.get("/api/v1/preloaded-scenes/calle-mayor").status_code == 404


@pytest.mark.parametrize("content", ["{bad", "{}", '[{"title":"bad"}]'])
def test_bad_storage(client: TestClient, path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    for url in ["/api/v1/preloaded-scenes", "/api/v1/preloaded-scenes/calle-mayor"]:
        response = client.get(url)
        assert response.status_code == 500
        assert response.json()["detail"]["code"] == "scene_storage_error"


@pytest.mark.parametrize("mutation", ["duplicate", "reference", "coordinates"])
def test_invalid_scene_content(path: Path, mutation: str) -> None:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "duplicate":
        rows.append(rows[0])
    elif mutation == "reference":
        rows[0]["tasks"][0]["itemIds"] = ["unknown"]
    else:
        rows[0]["items"][0]["x"] = 101
    path.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(SceneStorageError):
        JsonSceneRepository(path).list_scenes()


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SceneStorageError):
        JsonSceneRepository(tmp_path / "missing.json").list_scenes()
