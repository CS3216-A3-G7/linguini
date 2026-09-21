from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_active_language,
    get_learning_service,
    get_media_asset_repository,
    get_practice_service,
)
from app.api.errors import service_not_implemented
from app.config import get_media_public_base_url, get_private_media_urls
from app.repositories.media_assets import MediaAssetRepository
from app.schemas.home import HomeActiveSession, HomeResponse, HomeSummaryResponse
from app.services.learning import LearningService, ProgressNotFoundError
from app.services.media_urls import public_media_url
from app.services.practice import PracticeService

router = APIRouter(tags=["home"])


@router.get("/home", response_model=HomeResponse)
async def get_home() -> HomeResponse:
    service_not_implemented("Get home summary")


@router.get("/me/home", response_model=HomeSummaryResponse)
def get_home_summary(
    learning: Annotated[LearningService, Depends(get_learning_service)],
    practice: Annotated[PracticeService, Depends(get_practice_service)],
    language: Annotated[str, Depends(get_active_language)],
    media: Annotated[MediaAssetRepository, Depends(get_media_asset_repository)],
) -> HomeSummaryResponse:
    try:
        xp = learning.get_progress(language).xp
    except ProgressNotFoundError:
        xp = 0
    active_session = None
    detail = practice.active()
    if detail is not None:
        asset = media.get_by_ids([detail.session.scene_media_asset_id]).get(
            detail.session.scene_media_asset_id
        )
        image_url = None
        if asset is not None:
            signer = get_private_media_urls()
            image_url = (
                signer.resolve([asset.storage_key]).get(asset.storage_key)
                if signer
                else public_media_url(asset.storage_key, get_media_public_base_url())
            )
        active_session = HomeActiveSession(
            id=detail.session.id,
            status=detail.session.status,
            title=detail.title,
            media_asset_id=detail.session.scene_media_asset_id,
            image_url=image_url,
            completed_task_count=detail.progress.completed_task_count
            if detail.progress
            else 0,
            total_task_count=detail.progress.total_task_count if detail.progress else 0,
        )
    return HomeSummaryResponse(
        xp=xp,
        vocabulary_count=learning.count_vocabulary(language),
        active_session=active_session,
    )
