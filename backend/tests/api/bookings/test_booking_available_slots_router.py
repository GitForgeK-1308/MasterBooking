import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.models import (
    Booking,
    BookingStatus,
)
from src.master_offering.models import MasterOffering
from src.master_schedule.models import MasterSchedule
from src.masters.models import Master


@pytest.mark.anyio
async def test_get_available_slots(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    booking_schedule: MasterSchedule,
    future_booking_date: date,
):
    response = await ac.get(
        f"/masters/{master.id}/available-slots",
        params={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

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

    assert data["slots"] == [
        "09:00:00",
        "09:30:00",
        "10:00:00",
        "10:30:00",
        "11:00:00",
        "11:30:00",
        "12:00:00",
        "12:30:00",
        "13:00:00",
        "13:30:00",
        "14:00:00",
        "14:30:00",
        "15:00:00",
        "15:30:00",
        "16:00:00",
    ]


@pytest.mark.anyio
async def test_available_slots_exclude_conflicting_booking(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    booking_schedule: MasterSchedule,
    booking: Booking,
    future_booking_date: date,
):
    response = await ac.get(
        f"/masters/{master.id}/available-slots",
        params={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
        },
    )

    assert response.status_code == 200

    slots = response.json()["slots"]

    assert "09:00:00" in slots
    assert "09:30:00" not in slots
    assert "10:00:00" not in slots
    assert "10:30:00" not in slots
    assert "11:00:00" in slots

    assert len(slots) == 12


@pytest.mark.anyio
async def test_cancelled_booking_does_not_block_slots(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    booking_schedule: MasterSchedule,
    booking: Booking,
    future_booking_date: date,
    db_session: AsyncSession,
):
    booking.status = BookingStatus.CANCELLED

    await db_session.commit()

    response = await ac.get(
        f"/masters/{master.id}/available-slots",
        params={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
        },
    )

    assert response.status_code == 200

    slots = response.json()["slots"]

    assert "09:30:00" in slots
    assert "10:00:00" in slots
    assert "10:30:00" in slots

    assert len(slots) == 15


@pytest.mark.anyio
async def test_available_slots_in_past(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
):
    past_date = (
        date.today()
        - timedelta(
            days=1
        )
    )

    response = await ac.get(
        f"/masters/{master.id}/available-slots",
        params={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                past_date.isoformat()
            ),
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Нельзя получить слоты "
            "на прошедшую дату!"
        )
    }


@pytest.mark.anyio
async def test_available_slots_master_not_found(
    ac: AsyncClient,
    offering: MasterOffering,
    future_booking_date: date,
):
    response = await ac.get(
        (
            f"/masters/"
            f"{uuid.uuid4()}/available-slots"
        ),
        params={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Мастер не найден!"
    }


@pytest.mark.anyio
async def test_available_slots_inactive_master(
    ac: AsyncClient,
    inactive_master: Master,
    offering: MasterOffering,
    future_booking_date: date,
):
    response = await ac.get(
        (
            f"/masters/"
            f"{inactive_master.id}/available-slots"
        ),
        params={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Мастер сейчас не принимает записи!"
        )
    }


@pytest.mark.anyio
async def test_available_slots_offering_not_found(
    ac: AsyncClient,
    master: Master,
    future_booking_date: date,
):
    response = await ac.get(
        f"/masters/{master.id}/available-slots",
        params={
            "offering_id": str(
                uuid.uuid4()
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Услуга не найдена!"
    }


@pytest.mark.anyio
async def test_available_slots_inactive_offering(
    ac: AsyncClient,
    master: Master,
    inactive_offering: MasterOffering,
    future_booking_date: date,
):
    response = await ac.get(
        f"/masters/{master.id}/available-slots",
        params={
            "offering_id": str(
                inactive_offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Услуга сейчас недоступна!"
        )
    }


@pytest.mark.anyio
async def test_available_slots_offering_from_other_master(
    ac: AsyncClient,
    master: Master,
    second_master_offering: MasterOffering,
    future_booking_date: date,
):
    response = await ac.get(
        f"/masters/{master.id}/available-slots",
        params={
            "offering_id": str(
                second_master_offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
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
async def test_available_slots_schedule_unavailable(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    future_booking_date: date,
):
    response = await ac.get(
        f"/masters/{master.id}/available-slots",
        params={
            "offering_id": str(
                offering.id
            ),
            "booking_date": (
                future_booking_date.isoformat()
            ),
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Мастер не работает "
            "в выбранный день!"
        )
    }