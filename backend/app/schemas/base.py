"""Shared Pydantic schema foundations."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Any, Generic, TypeAlias, TypeVar
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


LanguageCode: TypeAlias = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=2,
        max_length=35,
        pattern=r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$",
    ),
]
NonEmptyText: TypeAlias = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1)
]
JsonObject: TypeAlias = dict[str, Any]
UnitScore: TypeAlias = Annotated[Decimal, Field(ge=0, le=1)]


class ApiModel(BaseModel):
    """Use snake_case in Python and camelCase in API JSON."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
        from_attributes=True,
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class EntityModel(ApiModel):
    """Common fields for persisted domain entities."""

    id: UUID = Field(default_factory=uuid4)
    created_at: AwareDatetime = Field(default_factory=utc_now)
    updated_at: AwareDatetime = Field(default_factory=utc_now)


class ApiErrorDetail(ApiModel):
    field: str | None = None
    message: NonEmptyText


class ApiErrorResponse(ApiModel):
    code: NonEmptyText
    message: NonEmptyText
    request_id: str | None = None
    details: list[ApiErrorDetail] = Field(default_factory=list)


PageItem = TypeVar("PageItem")


class CursorPage(ApiModel, Generic[PageItem]):
    items: list[PageItem]
    next_cursor: str | None = None
