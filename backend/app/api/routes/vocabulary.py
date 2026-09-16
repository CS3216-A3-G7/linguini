from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.errors import service_not_implemented
from app.schemas.base import CursorPage
from app.schemas.vocabulary import DailyVocabularyItem, DailyVocabularyResponse

router = APIRouter(prefix="/me/vocabulary", tags=["vocabulary"])


@router.get("", response_model=CursorPage[DailyVocabularyItem])
async def list_vocabulary(
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> CursorPage[DailyVocabularyItem]:
    service_not_implemented("List learner vocabulary")


@router.get("/daily", response_model=DailyVocabularyResponse)
async def get_daily_vocabulary(local_date: date | None = None) -> DailyVocabularyResponse:
    service_not_implemented("Get daily vocabulary")


@router.get("/{vocabulary_item_id}", response_model=DailyVocabularyItem)
async def get_vocabulary_item(vocabulary_item_id: UUID) -> DailyVocabularyItem:
    service_not_implemented("Get learner vocabulary item")
