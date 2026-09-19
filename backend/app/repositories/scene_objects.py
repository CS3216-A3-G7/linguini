from typing import Protocol
from uuid import UUID

from app.schemas.media import ReviewSceneObjectsRequest, SceneObject


class SceneObjectNotFoundError(Exception):
    pass


class SceneObjectReviewConflictError(Exception):
    pass


class SceneObjectRepository(Protocol):
    def save_analysis(
        self, session_id: UUID, user_id: UUID, objects: list[SceneObject]
    ) -> list[SceneObject]: ...
    def list_for_session(self, session_id: UUID, user_id: UUID) -> list[SceneObject]: ...

    def review(
        self, session_id: UUID, user_id: UUID, request: ReviewSceneObjectsRequest
    ) -> None: ...
