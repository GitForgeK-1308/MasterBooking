import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.bookings.models import BookingStatus
from src.bookings.repository import BookingRepository
from src.reviews.exceptions import (
    BookingNotCompletedError,
    ReviewAccessDeniedError,
    ReviewAlreadyExistsError,
    ReviewBookingNotFoundError,
)
from src.reviews.models import Review
from src.reviews.repository import ReviewRepository
from src.reviews.schemas import ReviewCreate
from src.reviews.service import ReviewService


def make_booking(
    *,
    booking_id: uuid.UUID | None = None,
    client_id: uuid.UUID | None = None,
    master_id: uuid.UUID | None = None,
    status: BookingStatus = BookingStatus.COMPLETED,
):
    return SimpleNamespace(
        id=booking_id or uuid.uuid4(),
        client_id=client_id or uuid.uuid4(),
        master_id=master_id or uuid.uuid4(),
        status=status,
    )


def make_review(
    *,
    review_id: uuid.UUID | None = None,
    rating: int = 5,
    comment: str | None = "Отлично!",
):
    return SimpleNamespace(
        id=review_id or uuid.uuid4(),
        rating=rating,
        comment=comment,
        created_at=datetime(
            2026,
            8,
            20,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )


@pytest.fixture
def review_repository() -> AsyncMock:
    return AsyncMock(spec=ReviewRepository)


@pytest.fixture
def booking_repository() -> AsyncMock:
    return AsyncMock(spec=BookingRepository)


@pytest.fixture
def review_service(
    review_repository: AsyncMock,
    booking_repository: AsyncMock,
) -> ReviewService:
    return ReviewService(
        repository=review_repository,
        booking_repository=booking_repository,
    )


@pytest.mark.anyio
async def test_create_review(
    review_service: ReviewService,
    review_repository: AsyncMock,
    booking_repository: AsyncMock,
):
    client_id = uuid.uuid4()

    booking = make_booking(client_id=client_id)

    booking_repository.get_by_id.return_value = booking

    review_repository.get_by_booking_id.return_value = None

    review_repository.create.side_effect = lambda review: review

    data = ReviewCreate(
        rating=5,
        comment="Отличная работа!",
    )

    result = await review_service.create_review(
        booking_id=booking.id,
        client_id=client_id,
        data=data,
    )

    assert isinstance(
        result,
        Review,
    )

    assert result.booking_id == booking.id
    assert result.master_id == booking.master_id
    assert result.client_id == client_id
    assert result.rating == 5

    assert result.comment == "Отличная работа!"

    booking_repository.get_by_id.assert_awaited_once_with(booking.id)

    review_repository.get_by_booking_id.assert_awaited_once_with(booking.id)

    review_repository.create.assert_awaited_once_with(result)


@pytest.mark.anyio
async def test_create_review_booking_not_found(
    review_service: ReviewService,
    review_repository: AsyncMock,
    booking_repository: AsyncMock,
):
    booking_repository.get_by_id.return_value = None

    with pytest.raises(ReviewBookingNotFoundError):
        await review_service.create_review(
            booking_id=uuid.uuid4(),
            client_id=uuid.uuid4(),
            data=ReviewCreate(rating=5),
        )

    review_repository.get_by_booking_id.assert_not_awaited()
    review_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_review_access_denied(
    review_service: ReviewService,
    review_repository: AsyncMock,
    booking_repository: AsyncMock,
):
    booking = make_booking()

    booking_repository.get_by_id.return_value = booking

    with pytest.raises(ReviewAccessDeniedError):
        await review_service.create_review(
            booking_id=booking.id,
            client_id=uuid.uuid4(),
            data=ReviewCreate(rating=5),
        )

    review_repository.get_by_booking_id.assert_not_awaited()
    review_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_review_booking_not_completed(
    review_service: ReviewService,
    review_repository: AsyncMock,
    booking_repository: AsyncMock,
):
    client_id = uuid.uuid4()

    booking = make_booking(
        client_id=client_id,
        status=BookingStatus.CONFIRMED,
    )

    booking_repository.get_by_id.return_value = booking

    with pytest.raises(BookingNotCompletedError):
        await review_service.create_review(
            booking_id=booking.id,
            client_id=client_id,
            data=ReviewCreate(rating=5),
        )

    review_repository.get_by_booking_id.assert_not_awaited()
    review_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_review_already_exists(
    review_service: ReviewService,
    review_repository: AsyncMock,
    booking_repository: AsyncMock,
):
    client_id = uuid.uuid4()

    booking = make_booking(client_id=client_id)

    booking_repository.get_by_id.return_value = booking

    review_repository.get_by_booking_id.return_value = make_review()

    with pytest.raises(ReviewAlreadyExistsError):
        await review_service.create_review(
            booking_id=booking.id,
            client_id=client_id,
            data=ReviewCreate(rating=5),
        )

    review_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_get_public_master_reviews(
    review_service: ReviewService,
    review_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    first_review = make_review(
        rating=5,
        comment="Отлично!",
    )

    second_review = make_review(
        rating=4,
        comment="Хорошо.",
    )

    review_repository.get_public_by_master_id.return_value = [
        (
            first_review,
            "Ivan",
            "Ivanov",
        ),
        (
            second_review,
            "Petr",
            None,
        ),
    ]

    result = await review_service.get_public_master_reviews(master_id)

    assert len(result) == 2

    assert result[0].id == first_review.id
    assert result[0].rating == 5

    assert result[0].client_name == "Ivan Ivanov"

    assert result[1].id == second_review.id
    assert result[1].rating == 4

    assert result[1].client_name == "Petr"

    review_repository.get_public_by_master_id.assert_awaited_once_with(master_id)


@pytest.mark.anyio
async def test_get_public_master_reviews_deleted_user(
    review_service: ReviewService,
    review_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    review = make_review()

    review_repository.get_public_by_master_id.return_value = [
        (
            review,
            None,
            None,
        )
    ]

    result = await review_service.get_public_master_reviews(master_id)

    assert len(result) == 1

    assert result[0].client_name == "Удалённый пользователь"


@pytest.mark.anyio
async def test_get_master_stats(
    review_service: ReviewService,
    review_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    review_repository.get_master_stats.return_value = (
        4.3,
        7,
    )

    result = await review_service.get_master_stats(master_id)

    assert result.average_rating == 4.3
    assert result.reviews_count == 7

    review_repository.get_master_stats.assert_awaited_once_with(master_id)


@pytest.mark.anyio
async def test_get_master_reviews_with_stats(
    review_service: ReviewService,
    review_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    first_review = make_review(rating=5)

    second_review = make_review(rating=4)

    review_repository.get_public_by_master_id.return_value = [
        (
            first_review,
            "Ivan",
            "Ivanov",
        ),
        (
            second_review,
            "Petr",
            "Petrov",
        ),
    ]

    review_repository.get_master_stats.return_value = (
        4.5,
        2,
    )

    distribution = {
        1: 0,
        2: 0,
        3: 0,
        4: 1,
        5: 1,
    }

    review_repository.get_rating_distribution.return_value = distribution

    result = await review_service.get_master_reviews_with_stats(master_id)

    assert result.average_rating == 4.5
    assert result.reviews_count == 2

    assert result.rating_distribution == distribution

    assert len(result.reviews) == 2

    assert result.reviews[0].client_name == "Ivan Ivanov"

    assert result.reviews[1].client_name == "Petr Petrov"


@pytest.mark.anyio
async def test_get_reviews_for_master_dashboard(
    review_service: ReviewService,
    review_repository: AsyncMock,
):
    master_id = uuid.uuid4()
    offering_id = uuid.uuid4()

    review = make_review(
        rating=5,
        comment="Супер!",
    )

    review_repository.get_for_master_dashboard.return_value = [
        (
            review,
            offering_id,
            "Classic Cut",
            "Ivan",
            "Ivanov",
        )
    ]

    result = await review_service.get_reviews_for_master_dashboard(master_id)

    assert len(result) == 1

    assert result[0].id == review.id
    assert result[0].offering_id == offering_id

    assert result[0].offering_title == "Classic Cut"

    assert result[0].rating == 5

    assert result[0].comment == "Супер!"

    assert result[0].client_name == "Ivan Ivanov"

    review_repository.get_for_master_dashboard.assert_awaited_once_with(master_id)


@pytest.mark.anyio
async def test_get_reviews_for_master_dashboard_deleted_user(
    review_service: ReviewService,
    review_repository: AsyncMock,
):
    master_id = uuid.uuid4()
    offering_id = uuid.uuid4()

    review = make_review()

    review_repository.get_for_master_dashboard.return_value = [
        (
            review,
            offering_id,
            "Classic Cut",
            None,
            None,
        )
    ]

    result = await review_service.get_reviews_for_master_dashboard(master_id)

    assert result[0].client_name == "Удалённый пользователь"


@pytest.mark.parametrize(
    (
        "first_name",
        "last_name",
        "expected",
    ),
    [
        (
            "Ivan",
            "Ivanov",
            "Ivan Ivanov",
        ),
        (
            "Ivan",
            None,
            "Ivan",
        ),
        (
            None,
            None,
            "Удалённый пользователь",
        ),
    ],
)
def test_get_client_name(
    first_name: str | None,
    last_name: str | None,
    expected: str,
):
    result = ReviewService._get_client_name(
        first_name=first_name,
        last_name=last_name,
    )

    assert result == expected
