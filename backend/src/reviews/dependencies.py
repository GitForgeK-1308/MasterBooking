from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.repository import BookingRepository
from src.database.session import get_async_session
from src.reviews.repository import ReviewRepository
from src.reviews.service import ReviewService


def get_review_service(
    session: AsyncSession = Depends(
        get_async_session
    ),
) -> ReviewService:
    review_repository = ReviewRepository(
        session
    )

    booking_repository = BookingRepository(
        session
    )

    return ReviewService(
        repository=review_repository,
        booking_repository=booking_repository,
    )