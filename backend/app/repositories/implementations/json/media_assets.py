"""Read the media metadata embedded in the existing scene fixtures."""

import json
from pathlib import Path
from uuid import UUID

from pydantic import TypeAdapter, ValidationError

from app.repositories.media_assets import MediaAssetStorageError
from app.schemas.media import MediaAsset


def read_media_assets(path: Path, *, from_scenes: bool = True) -> list[MediaAsset]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Expected a JSON array.")
    records = TypeAdapter(list[MediaAsset]).validate_python(
        [row["mediaAsset"] for row in raw] if from_scenes else raw
    )
    unique: dict[UUID, MediaAsset] = {}
    keys: dict[str, UUID] = {}
    for asset in records:
        if asset.id in unique and unique[asset.id] != asset:
            raise ValueError("Conflicting metadata for a repeated media asset ID.")
        if asset.storage_key in keys and keys[asset.storage_key] != asset.id:
            raise ValueError("Duplicate media storage key.")
        unique[asset.id] = asset
        keys[asset.storage_key] = asset.id
    return list(unique.values())


class JsonMediaAssetRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def get_by_ids(self, asset_ids: list[UUID]) -> dict[UUID, MediaAsset]:
        if not asset_ids:
            return {}
        try:
            wanted = set(asset_ids)
            return {row.id: row for row in read_media_assets(self.path) if row.id in wanted}
        except (OSError, UnicodeError, ValueError, KeyError, TypeError, ValidationError) as exc:
            raise MediaAssetStorageError("Unable to read media assets.") from exc
