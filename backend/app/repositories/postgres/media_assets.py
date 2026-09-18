"""SQLAlchemy metadata persistence; only trusted server code may register assets."""

from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import (
    Column,
    DateTime,
    Engine,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    Uuid,
    insert,
    select,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.repositories.media_assets import MediaAssetConflictError, MediaAssetStorageError
from app.schemas.media import MediaAsset

media_assets = Table(
    "media_assets",
    MetaData(),
    Column("id", Uuid, primary_key=True),
    Column("owner_user_id", Uuid),
    Column("media_type", String(5), nullable=False),
    Column("source", String(10), nullable=False),
    Column("storage_key", Text, nullable=False),
    Column("mime_type", Text, nullable=False),
    Column("width", Integer),
    Column("height", Integer),
    Column("duration_ms", Integer),
    Column("captured_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    schema="public",
)


class PostgresMediaAssetRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def get_by_ids(self, asset_ids: list[UUID]) -> dict[UUID, MediaAsset]:
        if not asset_ids:
            return {}
        try:
            with self.engine.connect() as connection:
                rows = connection.execute(
                    select(media_assets).where(media_assets.c.id.in_(asset_ids))
                ).mappings()
                return {row["id"]: MediaAsset.model_validate(dict(row)) for row in rows}
        except (SQLAlchemyError, ValidationError) as exc:
            raise MediaAssetStorageError("Unable to read media assets.") from exc

    def create(self, asset: MediaAsset) -> MediaAsset:
        try:
            with self.engine.begin() as connection:
                row = (
                    connection.execute(
                        insert(media_assets)
                        .values(**asset.model_dump(by_alias=False))
                        .returning(media_assets)
                    )
                    .mappings()
                    .one()
                )
                return MediaAsset.model_validate(dict(row))
        except IntegrityError as exc:
            if getattr(exc.orig, "sqlstate", None) == "23505":
                raise MediaAssetConflictError("Media asset or storage key already exists.") from exc
            raise MediaAssetStorageError("Unable to save media asset.") from exc
        except (SQLAlchemyError, ValidationError) as exc:
            raise MediaAssetStorageError("Unable to save media asset.") from exc
