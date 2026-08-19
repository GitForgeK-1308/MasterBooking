import uuid
from datetime import (
    date,
    timedelta,
)

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.models import Booking
from src.bookings.repository import (
    BookingRepository,
)
from src.master_offering.models import MasterOffering
from src.master_schedule.models import MasterSchedule
from src.masters.models import Master
from src.users.models import User


@pytest.mark.anyio
async def test_create_booking(
    ac: AsyncClient,
    user: User,
    master: Master,
    offering: MasterOffering,
    booking_schedule: MasterSchedule,
    future_booking_date: date,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["client_id"] == str(
        user.id
    )

    assert data["master_id"] == str(
        master.id
    )

    assert data["offering_id"] == str(
        offering.id
    )

    assert (
        data["booking_date"]
        == future_booking_date.isoformat()
    )

    assert data["start_time"] == "10:00:00"
    assert data["end_time"] == "11:00:00"

    assert (
        data["client_name"]
        == (
            f"{user.first_name} "
            f"{user.last_name}"
        )
    )

    assert (
        data["client_phone"]
        == user.phone
    )

    assert (
        data["client_email"]
        == user.email
    )

    assert data["status"] == "pending"

    booking_id = uuid.UUID(
        data["id"]
    )

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
        booking_from_database.end_time.isoformat()
        == "11:00:00"
    )


@pytest.mark.anyio
async def test_create_booking_without_token(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    future_booking_date: date,
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_create_booking_as_master_forbidden(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    future_booking_date: date,
    master_auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=master_auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_booking_phone_required(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    future_booking_date: date,
    no_phone_auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=no_phone_auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Для бронирования необходимо "
            "указать номер телефона!"
        )
    }


@pytest.mark.anyio
async def test_create_booking_master_not_found(
    ac: AsyncClient,
    offering: MasterOffering,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        (
            f"/masters/"
            f"{uuid.uuid4()}/bookings"
        ),
        headers=auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Мастер не найден!"
    }


@pytest.mark.anyio
async def test_create_booking_inactive_master(
    ac: AsyncClient,
    inactive_master: Master,
    offering: MasterOffering,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        (
            f"/masters/"
            f"{inactive_master.id}/bookings"
        ),
        headers=auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Мастер сейчас не принимает записи!"
        )
    }


@pytest.mark.anyio
async def test_create_booking_offering_not_found(
    ac: AsyncClient,
    master: Master,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": str(
                uuid.uuid4()
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Услуга не найдена!"
    }


@pytest.mark.anyio
async def test_create_booking_inactive_offering(
    ac: AsyncClient,
    master: Master,
    inactive_offering: MasterOffering,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": str(
                inactive_offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Услуга сейчас недоступна!"
        )
    }


@pytest.mark.anyio
async def test_create_booking_offering_from_other_master(
    ac: AsyncClient,
    master: Master,
    second_master_offering: MasterOffering,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": str(
                second_master_offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Услуга не принадлежит "
            "выбранному мастеру!"
        )
    }


@pytest.mark.anyio
async def test_create_booking_schedule_unavailable(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Мастер не работает "
            "в выбранный день!"
        )
    }


@pytest.mark.anyio
async def test_create_booking_in_past(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    auth_headers: dict[str, str],
):
    past_date = (
        date.today()
        - timedelta(
            days=1
        )
    )

    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                past_date.isoformat()
            ),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Нельзя создать запись "
            "на прошедшее время!"
        )
    }


@pytest.mark.anyio
async def test_create_booking_before_working_hours(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    booking_schedule: MasterSchedule,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "08:30:00",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Выбранное время находится вне "
            "рабочего времени мастера!"
        )
    }


@pytest.mark.anyio
async def test_create_booking_ends_after_working_hours(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    booking_schedule: MasterSchedule,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "16:30:00",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Выбранное время находится вне "
            "рабочего времени мастера!"
        )
    }


@pytest.mark.anyio
async def test_create_booking_invalid_slot_start(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    booking_schedule: MasterSchedule,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "09:15:00",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Выбранное время не соответствует "
            "доступному шагу записи!"
        )
    }


@pytest.mark.anyio
async def test_create_booking_time_conflict(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    booking_schedule: MasterSchedule,
    booking: Booking,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "10:30:00",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Выбранное время уже занято!"
        )
    }


@pytest.mark.anyio
async def test_create_booking_adjacent_time_is_allowed(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    booking_schedule: MasterSchedule,
    booking: Booking,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "11:00:00",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["start_time"] == "11:00:00"
    assert data["end_time"] == "12:00:00"


@pytest.mark.anyio
async def test_create_booking_rejects_extra_fields(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "10:00:00",
            "unexpected": "value",
        },
    )

    assert response.status_code == 422