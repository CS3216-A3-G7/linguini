from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_active_language, get_scene_service
from app.api.errors import service_not_implemented
from app.schemas.media import (
    ConfirmMediaUploadRequest,
    CreateUploadUrlRequest,
    CreateUploadUrlResponse,
    MediaAsset,
    PreloadedScene,
)
from app.schemas.scenes import PreloadedSceneDetail
from app.services.scenes import SceneService

router = APIRouter(tags=["media"])


@router.post("/media/upload-url", response_model=CreateUploadUrlResponse)
async def create_upload_url(request: CreateUploadUrlRequest) -> CreateUploadUrlResponse:
    service_not_implemented("Create signed media upload URL")


@router.post(
    "/media/confirm-upload",
    response_model=MediaAsset,
    status_code=status.HTTP_201_CREATED,
)
async def confirm_upload(request: ConfirmMediaUploadRequest) -> MediaAsset:
    service_not_implemented("Confirm media upload")


@router.get("/preloaded-scenes", response_model=list[PreloadedScene])
def list_preloaded_scenes(
    service: Annotated[SceneService, Depends(get_scene_service)],
    language: Annotated[str, Depends(get_active_language)],
) -> list[PreloadedScene]:
    return service.list_scenes(language)


@router.get("/preloaded-scenes/{scene_id}", response_model=PreloadedSceneDetail)
def get_preloaded_scene(
    scene_id: str,
    service: Annotated[SceneService, Depends(get_scene_service)],
    language: Annotated[str, Depends(get_active_language)],
) -> PreloadedSceneDetail:
    return service.get_scene(scene_id, language)
