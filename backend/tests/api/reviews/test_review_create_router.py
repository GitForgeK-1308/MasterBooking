import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.models import Booking
from src.masters.models import Master
from src.reviews.models import Review
from src.reviews.repository import ReviewRepository
from src.users.models import User


@pytest.mark.anyio
async def test_create_review(
    ac: AsyncClient,
    user: User,
    completed_booking: Booking,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.post(
        (
            f"/bookings/"
            f"{completed_booking.id}/review"
        ),
        headers=auth_headers,
        json={
            "rating": 5,
            "comment": "Отличная работа!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert (
        data["booking_id"]
        == str(completed_booking.id)
    )

    assert (
        data["master_id"]
        == str(completed_booking.master_id)
    )

    assert data["client_id"] == str(
        user.id
    )

    assert data["rating"] == 5

    assert (
        data["comment"]
        == "Отличная работа!"
    )

    review_id = uuid.UUID(
        data["id"]
    )

    repository = ReviewRepository(
        db_session
    )

    review_from_database = (
        await repository.get_by_id(
            review_id
        )
    )

    assert review_from_database is not None

    assert (
        review_from_database.booking_id
        == completed_booking.id
    )

    assert (
        review_from_database.rating
        == 5
    )


@pytest.mark.anyio
async def test_create_review_without_comment(
    ac: AsyncClient,
    completed_booking: Booking,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        (
            f"/bookings/"
            f"{completed_booking.id}/review"
        ),
        headers=auth_headers,
        json={
            "rating": 4,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["rating"] == 4
    assert data["comment"] is None


@pytest.mark.anyio
async def test_create_review_without_token(
    ac: AsyncClient,
    completed_booking: Booking,
):
    response = await ac.post(
        (
            f"/bookings/"
            f"{completed_booking.id}/review"
        ),
        json={
            "rating": 5,
            "comment": "Отлично",
        },
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_review_as_master_forbidden(
    ac: AsyncClient,
    master: Master,
    completed_booking: Booking,
    master_auth_headers: dict[str, str],
):
    response = await ac.post(
        (
            f"/bookings/"
            f"{completed_booking.id}/review"
        ),
        headers=master_auth_headers,
        json={
            "rating": 5,
            "comment": "Отлично",
        },
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_review_booking_not_found(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/bookings/{uuid.uuid4()}/review",
        headers=auth_headers,
        json={
            "rating": 5,
            "comment": "Отлично",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Запись не найдена!"
    }


@pytest.mark.anyio
async def test_create_review_for_foreign_booking_forbidden(
    ac: AsyncClient,
    foreign_completed_booking: Booking,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        (
            f"/bookings/"
            f"{foreign_completed_booking.id}/review"
        ),
        headers=auth_headers,
        json={
            "rating": 5,
            "comment": "Отлично",
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Вы не можете оставить отзыв "
            "для чужой записи!"
        )
    }


@pytest.mark.anyio
async def test_create_review_booking_not_completed(
    ac: AsyncClient,
    booking: Booking,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/bookings/{booking.id}/review",
        headers=auth_headers,
        json={
            "rating": 5,
            "comment": "Отлично",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Отзыв можно оставить только "
            "после завершения записи!"
        )
    }


@pytest.mark.anyio
async def test_create_second_review_rejected(
    ac: AsyncClient,
    completed_booking: Booking,
    review: Review,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        (
            f"/bookings/"
            f"{completed_booking.id}/review"
        ),
        headers=auth_headers,
        json={
            "rating": 4,
            "comment": "Ещё один отзыв",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Для этой записи отзыв "
            "уже оставлен!"
        )
    }


@pytest.mark.anyio
async def test_create_review_rating_below_minimum(
    ac: AsyncClient,
    completed_booking: Booking,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        (
            f"/bookings/"
            f"{completed_booking.id}/review"
        ),
        headers=auth_headers,
        json={
            "rating": 0,
            "comment": "Плохо",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_review_rating_above_maximum(
    ac: AsyncClient,
    completed_booking: Booking,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        (
            f"/bookings/"
            f"{completed_booking.id}/review"
        ),
        headers=auth_headers,
        json={
            "rating": 6,
            "comment": "Слишком хорошо",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_review_comment_too_long(
    ac: AsyncClient,
    completed_booking: Booking,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        (
            f"/bookings/"
            f"{completed_booking.id}/review"
        ),
        headers=auth_headers,
        json={
            "rating": 5,
            "comment": "x" * 1001,
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_review_rejects_extra_fields(
    ac: AsyncClient,
    completed_booking: Booking,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        (
            f"/bookings/"
            f"{completed_booking.id}/review"
        ),
        headers=auth_headers,
        json={
            "rating": 5,
            "comment": "Отлично",
            "unexpected": "value",
        },
    )

    assert response.status_code == 422