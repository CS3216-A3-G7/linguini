from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import (
    Column,
    DateTime,
    Engine,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    Uuid,
    insert,
    select,
    update,
)
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.postgres.practice import sessions
from app.repositories.postgres.users import users
from app.repositories.practice import PracticeStorageError
from app.repositories.scene_objects import SceneObjectNotFoundError, SceneObjectReviewConflictError
from app.schemas.enums import SessionStatus
from app.schemas.media import ReviewSceneObjectsRequest, SceneObject

scene_objects = Table(
    "scene_objects",
    MetaData(),
    Column("id", Uuid, primary_key=True),
    Column("session_id", Uuid, nullable=False),
    Column("media_asset_id", Uuid, nullable=False),
    Column("detected_label", Text, nullable=False),
    Column("confirmed_label", String(200)),
    Column("selection_status", String(9), nullable=False),
    *[Column(name, Numeric(10, 9), nullable=False) for name in ("x", "y", "width", "height")],
    Column("confidence", Numeric(6, 5)),
    Column("vocabulary_item_id", Uuid),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    schema="public",
)


def object_values(item: SceneObject) -> dict:
    values = item.model_dump(by_alias=False)
    bounding_box = values.pop("bounding_box")
    return values | bounding_box


def parse_object(row) -> SceneObject:
    values = dict(row)
    values["bounding_box"] = {key: values.pop(key) for key in ("x", "y", "width", "height")}
    return SceneObject.model_validate(values)


class PostgresSceneObjectRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def list_for_session(self, session_id: UUID, user_id: UUID) -> list[SceneObject]:
        try:
            with self.engine.connect() as connection:
                return [
                    parse_object(row)
                    for row in connection.execute(
                        select(scene_objects)
                        .join(sessions, sessions.c.id == scene_objects.c.session_id)
                        .where(sessions.c.id == session_id, sessions.c.user_id == user_id)
                        .order_by(scene_objects.c.created_at, scene_objects.c.id)
                    ).mappings()
                ]
        except (SQLAlchemyError, ValidationError) as exc:
            raise PracticeStorageError("Unable to load scene objects.") from exc

    def create(self, item: SceneObject) -> SceneObject:
        """Trusted detector/import metadata, never arbitrary frontend detections."""
        try:
            with self.engine.begin() as connection:
                return parse_object(
                    connection.execute(
                        insert(scene_objects).values(**object_values(item)).returning(scene_objects)
                    )
                    .mappings()
                    .one()
                )
        except (SQLAlchemyError, ValidationError) as exc:
            raise PracticeStorageError("Unable to save scene object.") from exc

    def save_analysis(
        self, session_id: UUID, user_id: UUID, objects: list[SceneObject]
    ) -> list[SceneObject]:
        """Persist one complete result atomically; retries preserve reviewed objects."""
        try:
            with self.engine.begin() as connection:
                # Match the lock order used by session writes and object review.
                connection.execute(
                    select(users.c.id).where(users.c.id == user_id).with_for_update()
                )
                session = (
                    connection.execute(
                        select(sessions)
                        .where(
                            sessions.c.id == session_id,
                            sessions.c.user_id == user_id,
                        )
                        .with_for_update()
                    )
                    .mappings()
                    .one_or_none()
                )
                if session is None:
                    raise SceneObjectNotFoundError("Session not found.")
                if session["status"] != SessionStatus.IN_PROGRESS:
                    raise SceneObjectReviewConflictError("Session is no longer active.")
                existing = (
                    connection.execute(
                        select(scene_objects)
                        .where(
                            scene_objects.c.session_id == session_id,
                        )
                        .order_by(scene_objects.c.created_at, scene_objects.c.id)
                    )
                    .mappings()
                    .all()
                )
                if existing:
                    return [parse_object(row) for row in existing]
                if not objects or any(
                    obj.session_id != session_id
                    or obj.media_asset_id != session["scene_media_asset_id"]
                    for obj in objects
                ):
                    raise PracticeStorageError("Invalid analysis result.")
                connection.execute(insert(scene_objects), [object_values(obj) for obj in objects])
                return objects
        except (SQLAlchemyError, ValidationError) as exc:
            raise PracticeStorageError("Unable to save analysis.") from exc

    def review(self, session_id: UUID, user_id: UUID, request: ReviewSceneObjectsRequest) -> None:
        try:
            with self.engine.begin() as connection:
                connection.execute(
                    select(users.c.id).where(users.c.id == user_id).with_for_update()
                ).scalar_one_or_none()
                session = (
                    connection.execute(
                        select(sessions)
                        .where(sessions.c.id == session_id, sessions.c.user_id == user_id)
                        .with_for_update()
                    )
                    .mappings()
                    .one_or_none()
                )
                if session is None:
                    raise SceneObjectNotFoundError("Session not found.")
                if session["status"] in {"completed", "abandoned", "failed"}:
                    raise SceneObjectReviewConflictError(
                        "Cannot review objects in a terminal session."
                    )
                for item in request.objects:
                    values = {
                        "selection_status": item.selection_status,
                        "confirmed_label": item.confirmed_label,
                    }
                    found = connection.execute(
                        update(scene_objects)
                        .where(
                            scene_objects.c.session_id == session_id,
                            scene_objects.c.id == item.scene_object_id,
                        )
                        .values(**values)
                        .returning(scene_objects.c.id)
                    ).scalar_one_or_none()
                    if found is None:
                        raise SceneObjectNotFoundError("Scene object not found in this session.")
        except (SQLAlchemyError, ValidationError) as exc:
            raise PracticeStorageError("Unable to review scene objects.") from exc
