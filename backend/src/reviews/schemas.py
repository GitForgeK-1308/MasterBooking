import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class ReviewCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    rating: int = Field(
        ge=1,
        le=5,
    )

    comment: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
    )


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    master_id: uuid.UUID
    client_id: uuid.UUID | None

    rating: int
    comment: str | None

    created_at: datetime


class ReviewStatsResponse(BaseModel):
    average_rating: float
    reviews_count: int


class ReviewPublicResponse(BaseModel):
    id: uuid.UUID

    rating: int
    comment: str | None

    client_name: str
    created_at: datetime


class MasterReviewsResponse(BaseModel):
    average_rating: float
    reviews_count: int
    rating_distribution: dict[int, int]

    reviews: list[ReviewPublicResponse]


class MasterReviewResponse(BaseModel):
    id: uuid.UUID

    offering_id: uuid.UUID
    offering_title: str

    rating: int
    comment: str | None

    client_name: str
    created_at: datetime
