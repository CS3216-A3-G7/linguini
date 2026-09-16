from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from app.repositories.scenes import SceneStorageError
from app.schemas.scenes import PreloadedSceneDetail


class JsonSceneRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def list_scenes(self) -> list[PreloadedSceneDetail]:
        try:
            rows = TypeAdapter(list[PreloadedSceneDetail]).validate_json(
                self.path.read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError, ValidationError) as exc:
            raise SceneStorageError("Unable to load scenes.") from exc
        if len({row.scene_id for row in rows}) != len(rows):
            raise SceneStorageError("Duplicate scene ID.")
        return rows
