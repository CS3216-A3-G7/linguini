from fastapi import APIRouter, status

from app.api.errors import service_not_implemented
from app.schemas.media import (
    ConfirmMediaUploadRequest,
    CreateUploadUrlRequest,
    CreateUploadUrlResponse,
    MediaAsset,
    PreloadedScene,
)

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
async def list_preloaded_scenes() -> list[PreloadedScene]:
    service_not_implemented("List preloaded scenes")
