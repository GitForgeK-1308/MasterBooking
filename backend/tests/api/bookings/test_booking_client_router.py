import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.models import (
    Booking,
    BookingStatus,
)
from src.bookings.repository import (
    BookingRepository,
)
from src.users.models import User


@pytest.mark.anyio
async def test_get_my_bookings(
    ac: AsyncClient,
    user: User,
    booking: Booking,
    second_booking: Booking,
    foreign_booking: Booking,
    auth_headers: dict[str, str],
):
    response = await ac.get(
        "/users/me/bookings",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert [
        item["id"]
        for item in data
    ] == [
        str(booking.id),
        str(second_booking.id),
    ]

    assert all(
        item["client_id"]
        == str(user.id)
        for item in data
    )

    assert str(
        foreign_booking.id
    ) not in {
        item["id"]
        for item in data
    }


@pytest.mark.anyio
async def test_get_my_bookings_without_token(
    ac: AsyncClient,
):
    response = await ac.get(
        "/users/me/bookings"
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_booking_by_id_as_client(
    ac: AsyncClient,
    user: User,
    booking: Booking,
    auth_headers: dict[str, str],
):
    response = await ac.get(
        f"/bookings/{booking.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(
        booking.id
    )

    assert data["client_id"] == str(
        user.id
    )

    assert data["status"] == "pending"


@pytest.mark.anyio
async def test_get_booking_by_id_not_found(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.get(
        f"/bookings/{uuid.uuid4()}",
        headers=auth_headers,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Бронирование не найдено!"
    }


@pytest.mark.anyio
async def test_get_foreign_booking_forbidden(
    ac: AsyncClient,
    foreign_booking: Booking,
    auth_headers: dict[str, str],
):
    response = await ac.get(
        f"/bookings/{foreign_booking.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "У вас нет доступа "
            "к этому бронированию!"
        )
    }


@pytest.mark.anyio
async def test_get_booking_without_token(
    ac: AsyncClient,
    booking: Booking,
):
    response = await ac.get(
        f"/bookings/{booking.id}"
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_cancel_pending_booking(
    ac: AsyncClient,
    booking: Booking,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    booking_id = booking.id

    response = await ac.patch(
        (
            "/users/me/bookings/"
            f"{booking_id}/cancel"
        ),
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(
        booking_id
    )

    assert data["status"] == "cancelled"

    repository = BookingRepository(
        db_session
    )

    booking_from_database = (
        await repository.get_by_id(
            booking_id
        )
    )

    assert booking_from_database is not None

    assert (
        booking_from_database.status
        == BookingStatus.CANCELLED
    )


@pytest.mark.anyio
async def test_cancel_confirmed_booking(
    ac: AsyncClient,
    second_booking: Booking,
    auth_headers: dict[str, str],
):
    assert (
        second_booking.status
        == BookingStatus.CONFIRMED
    )

    response = await ac.patch(
        (
            "/users/me/bookings/"
            f"{second_booking.id}/cancel"
        ),
        headers=auth_headers,
    )

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "cancelled"
    )


@pytest.mark.anyio
async def test_cancel_completed_booking_rejected(
    ac: AsyncClient,
    booking: Booking,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    booking.status = BookingStatus.COMPLETED

    await db_session.commit()

    response = await ac.patch(
        (
            "/users/me/bookings/"
            f"{booking.id}/cancel"
        ),
        headers=auth_headers,
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Это бронирование нельзя отменить!"
        )
    }


@pytest.mark.anyio
async def test_cancel_already_cancelled_booking_rejected(
    ac: AsyncClient,
    booking: Booking,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    booking.status = BookingStatus.CANCELLED

    await db_session.commit()

    response = await ac.patch(
        (
            "/users/me/bookings/"
            f"{booking.id}/cancel"
        ),
        headers=auth_headers,
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Это бронирование нельзя отменить!"
        )
    }


@pytest.mark.anyio
async def test_cancel_foreign_booking_forbidden(
    ac: AsyncClient,
    foreign_booking: Booking,
    auth_headers: dict[str, str],
):
    response = await ac.patch(
        (
            "/users/me/bookings/"
            f"{foreign_booking.id}/cancel"
        ),
        headers=auth_headers,
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Вы не можете отменить "
            "чужое бронирование!"
        )
    }


@pytest.mark.anyio
async def test_cancel_booking_not_found(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.patch(
        (
            "/users/me/bookings/"
            f"{uuid.uuid4()}/cancel"
        ),
        headers=auth_headers,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Бронирование не найдено!"
    }


@pytest.mark.anyio
async def test_cancel_booking_without_token(
    ac: AsyncClient,
    booking: Booking,
):
    response = await ac.patch(
        (
            "/users/me/bookings/"
            f"{booking.id}/cancel"
        )
    )

    assert response.status_code == 401