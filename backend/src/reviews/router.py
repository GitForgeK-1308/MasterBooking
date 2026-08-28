import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from src.auth.dependencies import (
    get_current_customer,
    get_current_master_profile,
)
from src.masters.models import Master
from src.reviews.dependencies import get_review_service
from src.reviews.exceptions import (
    BookingNotCompletedError,
    ReviewAccessDeniedError,
    ReviewAlreadyExistsError,
    ReviewBookingNotFoundError,
)
from src.reviews.schemas import (
    MasterReviewResponse,
    MasterReviewsResponse,
    ReviewCreate,
    ReviewPublicResponse,
    ReviewResponse,
    ReviewStatsResponse,
)
from src.reviews.service import ReviewService
from src.users.models import User

router = APIRouter(tags=["Reviews"])


@router.post(
    "/bookings/{booking_id}/review",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    booking_id: uuid.UUID,
    data: ReviewCreate,
    current_customer: User = Depends(get_current_customer),
    service: ReviewService = Depends(get_review_service),
):
    try:
        return await service.create_review(
            booking_id=booking_id,
            client_id=current_customer.id,
            data=data,
        )

    except ReviewBookingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись не найдена!",
        ) from None

    except ReviewAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=("Вы не можете оставить отзыв для чужой записи!"),
        ) from None

    except BookingNotCompletedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Отзыв можно оставить только после завершения записи!"),
        ) from None

    except ReviewAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Для этой записи отзыв уже оставлен!"),
        ) from None


@router.get(
    "/masters/me/reviews",
    response_model=list[MasterReviewResponse],
)
async def get_my_reviews(
    current_master: Master = Depends(get_current_master_profile),
    service: ReviewService = Depends(get_review_service),
):
    return await service.get_reviews_for_master_dashboard(master_id=current_master.id)


@router.get(
    "/masters/{master_id}/reviews",
    response_model=list[ReviewPublicResponse],
)
async def get_master_reviews(
    master_id: uuid.UUID,
    service: ReviewService = Depends(get_review_service),
):
    return await service.get_public_master_reviews(master_id)


@router.get(
    "/masters/{master_id}/reviews/stats",
    response_model=ReviewStatsResponse,
)
async def get_master_review_stats(
    master_id: uuid.UUID,
    service: ReviewService = Depends(get_review_service),
):
    return await service.get_master_stats(master_id)


@router.get(
    "/masters/{master_id}/reviews/full",
    response_model=MasterReviewsResponse,
)
async def get_master_reviews_with_stats(
    master_id: uuid.UUID,
    service: ReviewService = Depends(get_review_service),
):
    return await service.get_master_reviews_with_stats(master_id)
