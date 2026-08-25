import uuid
from decimal import Decimal
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from src.tags.schemas import TagResponse


class OfferingSort(str, Enum):
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    POPULAR = "popular"


class MasterOfferingBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(
        min_length=2,
        max_length=100,
    )
    description: str = Field(
        min_length=1,
    )
    price: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
    )

    discount_percent: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    duration_minutes: int = Field(
        gt=0,
    )


class MasterOfferingCreate(MasterOfferingBase):
    category_id: uuid.UUID

    tag_ids: list[uuid.UUID] = Field(
        default_factory=list,
        max_length=10,
    )


class MasterOfferingUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    category_id: uuid.UUID | None = None

    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        min_length=1,
    )
    price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=10,
        decimal_places=2,
    )

    discount_percent: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    duration_minutes: int | None = Field(
        default=None,
        gt=0,
    )

    tag_ids: list[uuid.UUID] | None = Field(
        default=None,
        max_length=10,
    )


class OfferingMasterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str

    city_id: uuid.UUID | None
    district_id: uuid.UUID | None

    city: str | None
    district: str | None
    address: str | None

    phone: str | None
    avatar_url: str | None


class MasterOfferingResponse(MasterOfferingBase):
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )

    id: uuid.UUID
    category_id: uuid.UUID | None
    master_id: uuid.UUID

    tags: list[TagResponse] = Field(default_factory=list)
    final_price: Decimal
    master: OfferingMasterResponse

    is_active: bool


class MasterOfferingPage(BaseModel):
    items: list[MasterOfferingResponse]

    total: int
    page: int
    page_size: int
    total_pages: int
