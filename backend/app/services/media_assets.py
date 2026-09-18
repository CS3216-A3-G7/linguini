from uuid import UUID

from app.repositories.media_assets import MediaAssetRepository
from app.schemas.enums import MediaSource
from app.schemas.media import MediaAsset
from app.services.users import UserService


class MediaAssetNotFoundError(Exception):
    pass


class MediaAssetService:
    def __init__(self, repository: MediaAssetRepository, users: UserService) -> None:
        self.repository = repository
        self.users = users

    def get_asset(self, asset_id: UUID) -> MediaAsset:
        user = self.users.get_current_user()
        asset = self.repository.get_by_ids([asset_id]).get(asset_id)
        if asset is None or not (
            asset.owner_user_id == user.id or asset.source is MediaSource.PRELOADED
        ):
            raise MediaAssetNotFoundError("Media asset not found.")
        return asset
