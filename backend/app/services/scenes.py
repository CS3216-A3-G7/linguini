from app.repositories.scenes import SceneRepository
from app.schemas.media import PreloadedScene
from app.schemas.scenes import PreloadedSceneDetail


class SceneNotFoundError(Exception):
    pass


class SceneService:
    def __init__(self, repository: SceneRepository) -> None:
        self.repository = repository

    def list_scenes(self, language_code: str | None = None) -> list[PreloadedScene]:
        return [
            PreloadedScene.model_validate(row.model_dump(include=set(PreloadedScene.model_fields)))
            for row in self.repository.list_scenes()
            if language_code is None or row.language_code.lower() == language_code
        ]

    def get_scene(self, scene_id: str, language_code: str | None = None) -> PreloadedSceneDetail:
        scene = next(
            (row for row in self.repository.list_scenes() if row.scene_id == scene_id), None
        )
        if scene is None or (
            language_code is not None and scene.language_code.lower() != language_code
        ):
            raise SceneNotFoundError("Scene not found.")
        return scene
