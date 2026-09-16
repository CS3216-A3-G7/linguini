from uuid import UUID

from fastapi import APIRouter, status

from app.api.errors import service_not_implemented
from app.schemas.users import (
    CreateLanguageProfileRequest,
    LanguageProfile,
    UpdateLanguageProfileRequest,
    UpdateUserRequest,
    User,
)

router = APIRouter(tags=["users"])


@router.get("/me", response_model=User)
async def get_me() -> User:
    service_not_implemented("Get current user")


@router.patch("/me", response_model=User)
async def update_me(request: UpdateUserRequest) -> User:
    service_not_implemented("Update current user")


@router.get("/me/language-profiles", response_model=list[LanguageProfile])
async def list_language_profiles() -> list[LanguageProfile]:
    service_not_implemented("List language profiles")


@router.post(
    "/me/language-profiles",
    response_model=LanguageProfile,
    status_code=status.HTTP_201_CREATED,
)
async def create_language_profile(
    request: CreateLanguageProfileRequest,
) -> LanguageProfile:
    service_not_implemented("Create language profile")


@router.patch(
    "/me/language-profiles/{profile_id}", response_model=LanguageProfile
)
async def update_language_profile(
    profile_id: UUID, request: UpdateLanguageProfileRequest
) -> LanguageProfile:
    service_not_implemented("Update language profile")
