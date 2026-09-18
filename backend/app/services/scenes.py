from app.repositories.media_assets import MediaAssetRepository, MediaAssetStorageError
from app.repositories.scenes import SceneRepository
from app.schemas.enums import MediaSource
from app.schemas.media import PreloadedScene
from app.schemas.scenes import PreloadedSceneDetail


class SceneNotFoundError(Exception):
    pass


class SceneService:
    def __init__(
        self, repository: SceneRepository, media: MediaAssetRepository | None = None
    ) -> None:
        self.repository = repository
        self.media = media

    def _hydrate_media(self, rows: list[PreloadedSceneDetail]) -> list[PreloadedSceneDetail]:
        if self.media is None:
            return rows
        assets = self.media.get_by_ids([row.media_asset.id for row in rows])
        result = []
        for row in rows:
            asset = assets.get(row.media_asset.id)
            if asset is None or asset.source is not MediaSource.PRELOADED:
                raise MediaAssetStorageError("Preloaded scene media is missing or not shared.")
            result.append(row.model_copy(update={"media_asset": asset}))
        return result

    def list_scenes(self, language_code: str | None = None) -> list[PreloadedScene]:
        return [
            PreloadedScene.model_validate(row.model_dump(include=set(PreloadedScene.model_fields)))
            for row in self._hydrate_media(
                [
                    row
                    for row in self.repository.list_scenes()
                    if language_code is None or row.language_code.lower() == language_code
                ]
            )
        ]

    def get_scene(self, scene_id: str, language_code: str | None = None) -> PreloadedSceneDetail:
        scene = next(
            (row for row in self.repository.list_scenes() if row.scene_id == scene_id), None
        )
        if scene is None or (
            language_code is not None and scene.language_code.lower() != language_code
        ):
            raise SceneNotFoundError("Scene not found.")
        return self._hydrate_media([scene])[0]
