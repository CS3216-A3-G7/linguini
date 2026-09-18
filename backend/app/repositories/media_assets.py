"""Media metadata lookup shared by scene hydration and ownership-aware reads."""

from typing import Protocol
from uuid import UUID

from app.schemas.media import MediaAsset


class MediaAssetStorageError(Exception):
    pass


class MediaAssetConflictError(Exception):
    pass


class MediaAssetRepository(Protocol):
    def get_by_ids(self, asset_ids: list[UUID]) -> dict[UUID, MediaAsset]: ...
