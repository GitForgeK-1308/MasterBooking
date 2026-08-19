import uuid
from datetime import date, time, timedelta

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
from src.master_offering.models import MasterOffering
from src.masters.models import Master
from src.users.models import User


@pytest.mark.anyio
async def test_get_my_master_bookings(
    ac: AsyncClient,
    master: Master,
    booking: Booking,
    second_booking: Booking,
    future_booking_date: date,
    master_auth_headers: dict[str, str],
):
    response = await ac.get(
        "/masters/me/bookings",
        headers=master_auth_headers,
        params={
            "booking_date": (
                future_booking_date.isoformat()
            )
        },
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
        item["master_id"]
        == str(master.id)
        for item in data
    )

    assert [
        item["start_time"]
        for item in data
    ] == [
        "10:00:00",
        "12:00:00",
    ]


@pytest.mark.anyio
async def test_get_my_master_bookings_other_date_empty(
    ac: AsyncClient,
    master: Master,
    booking: Booking,
    future_booking_date: date,
    master_auth_headers: dict[str, str],
):
    other_date = (
        future_booking_date
        + timedelta(
            days=1
        )
    )

    response = await ac.get(
        "/masters/me/bookings",
        headers=master_auth_headers,
        params={
            "booking_date": (
                other_date.isoformat()
            )
        },
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_my_master_bookings_requires_date(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.get(
        "/masters/me/bookings",
        headers=master_auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_my_master_bookings_without_token(
    ac: AsyncClient,
):
    response = await ac.get(
        "/masters/me/bookings",
        params={
            "booking_date": "2030-01-01"
        },
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_get_my_master_bookings_as_client_forbidden(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.get(
        "/masters/me/bookings",
        headers=auth_headers,
        params={
            "booking_date": "2030-01-01"
        },
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_get_booking_by_id_as_master(
    ac: AsyncClient,
    master: Master,
    booking: Booking,
    master_auth_headers: dict[str, str],
):
    response = await ac.get(
        f"/bookings/{booking.id}",
        headers=master_auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(
        booking.id
    )

    assert data["master_id"] == str(
        master.id
    )


@pytest.mark.anyio
async def test_get_booking_by_id_as_other_master_forbidden(
    ac: AsyncClient,
    booking: Booking,
    second_master: Master,
    second_master_auth_headers: dict[str, str],
):
    response = await ac.get(
        f"/bookings/{booking.id}",
        headers=second_master_auth_headers,
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "У вас нет доступа "
            "к этому бронированию!"
        )
    }


@pytest.mark.anyio
@pytest.mark.parametrize(
    (
        "initial_status",
        "new_status",
    ),
    [
        (
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED,
        ),
        (
            BookingStatus.PENDING,
            BookingStatus.CANCELLED,
        ),
        (
            BookingStatus.CONFIRMED,
            BookingStatus.COMPLETED,
        ),
        (
            BookingStatus.CONFIRMED,
            BookingStatus.CANCELLED,
        ),
    ],
)
async def test_update_booking_status_allowed(
    ac: AsyncClient,
    master: Master,
    booking: Booking,
    master_auth_headers: dict[str, str],
    db_session: AsyncSession,
    initial_status: BookingStatus,
    new_status: BookingStatus,
):
    booking.status = initial_status

    await db_session.commit()

    response = await ac.patch(
        (
            "/masters/me/bookings/"
            f"{booking.id}/status"
        ),
        headers=master_auth_headers,
        json={
            "status": new_status.value
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["status"]
        == new_status.value
    )

    repository = BookingRepository(
        db_session
    )

    booking_from_database = (
        await repository.get_by_id(
            booking.id
        )
    )

    assert booking_from_database is not None

    assert (
        booking_from_database.status
        == new_status
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    (
        "initial_status",
        "new_status",
    ),
    [
        (
            BookingStatus.PENDING,
            BookingStatus.COMPLETED,
        ),
        (
            BookingStatus.COMPLETED,
            BookingStatus.CANCELLED,
        ),
        (
            BookingStatus.CANCELLED,
            BookingStatus.CONFIRMED,
        ),
    ],
)
async def test_update_booking_status_invalid_transition(
    ac: AsyncClient,
    master: Master,
    booking: Booking,
    master_auth_headers: dict[str, str],
    db_session: AsyncSession,
    initial_status: BookingStatus,
    new_status: BookingStatus,
):
    booking.status = initial_status

    await db_session.commit()

    response = await ac.patch(
        (
            "/masters/me/bookings/"
            f"{booking.id}/status"
        ),
        headers=master_auth_headers,
        json={
            "status": new_status.value
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Недопустимое изменение "
            "статуса бронирования!"
        )
    }


@pytest.mark.anyio
async def test_update_booking_status_not_found(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        (
            "/masters/me/bookings/"
            f"{uuid.uuid4()}/status"
        ),
        headers=master_auth_headers,
        json={
            "status": "confirmed"
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Бронирование не найдено!"
    }


@pytest.mark.anyio
async def test_update_foreign_master_booking_forbidden(
    ac: AsyncClient,
    user: User,
    master: Master,
    second_master: Master,
    second_master_offering: MasterOffering,
    future_booking_date: date,
    master_auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    foreign_booking = Booking(
        client_id=user.id,
        master_id=second_master.id,
        offering_id=second_master_offering.id,
        booking_date=future_booking_date,
        start_time=time(
            15,
            0,
        ),
        end_time=time(
            16,
            30,
        ),
        client_name=(
            f"{user.first_name} "
            f"{user.last_name}"
        ),
        client_phone=user.phone,
        client_email=user.email,
        status=BookingStatus.PENDING,
    )

    db_session.add(
        foreign_booking
    )

    await db_session.commit()
    await db_session.refresh(
        foreign_booking
    )

    response = await ac.patch(
        (
            "/masters/me/bookings/"
            f"{foreign_booking.id}/status"
        ),
        headers=master_auth_headers,
        json={
            "status": "confirmed"
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Вы не можете изменять "
            "чужое бронирование!"
        )
    }


@pytest.mark.anyio
async def test_update_booking_status_without_token(
    ac: AsyncClient,
    booking: Booking,
):
    response = await ac.patch(
        (
            "/masters/me/bookings/"
            f"{booking.id}/status"
        ),
        json={
            "status": "confirmed"
        },
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_update_booking_status_as_client_forbidden(
    ac: AsyncClient,
    booking: Booking,
    auth_headers: dict[str, str],
):
    response = await ac.patch(
        (
            "/masters/me/bookings/"
            f"{booking.id}/status"
        ),
        headers=auth_headers,
        json={
            "status": "confirmed"
        },
    )

    assert response.status_code == 403