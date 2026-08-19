from datetime import date

import pytest
from httpx import AsyncClient

from src.bookings.models import Booking
from src.master_offering.models import MasterOffering
from src.masters.models import Master


@pytest.mark.anyio
async def test_create_booking_invalid_master_uuid(
    ac: AsyncClient,
    offering: MasterOffering,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        "/masters/not-a-uuid/bookings",
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

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_booking_invalid_offering_uuid(
    ac: AsyncClient,
    master: Master,
    future_booking_date: date,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": "not-a-uuid",
            "booking_date": (
                future_booking_date.isoformat()
            ),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_booking_invalid_date(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
    auth_headers: dict[str, str],
):
    response = await ac.post(
        f"/masters/{master.id}/bookings",
        headers=auth_headers,
        json={
            "offering_id": str(
                offering.id
            ),
            "booking_date": "not-a-date",
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_booking_invalid_start_time(
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
            "start_time": "not-a-time",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_available_slots_missing_offering_id(
    ac: AsyncClient,
    master: Master,
    future_booking_date: date,
):
    response = await ac.get(
        f"/masters/{master.id}/available-slots",
        params={
            "booking_date": (
                future_booking_date.isoformat()
            ),
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_available_slots_invalid_date(
    ac: AsyncClient,
    master: Master,
    offering: MasterOffering,
):
    response = await ac.get(
        f"/masters/{master.id}/available-slots",
        params={
            "offering_id": str(
                offering.id
            ),
            "booking_date": "not-a-date",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_booking_invalid_uuid(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.get(
        "/bookings/not-a-uuid",
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_cancel_booking_invalid_uuid(
    ac: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await ac.patch(
        "/users/me/bookings/not-a-uuid/cancel",
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_booking_invalid_status(
    ac: AsyncClient,
    booking: Booking,
    master_auth_headers: dict[str, str],
):
    response = await ac.patch(
        (
            "/masters/me/bookings/"
            f"{booking.id}/status"
        ),
        headers=master_auth_headers,
        json={
            "status": "unknown-status"
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_master_bookings_invalid_date(
    ac: AsyncClient,
    master: Master,
    master_auth_headers: dict[str, str],
):
    response = await ac.get(
        "/masters/me/bookings",
        headers=master_auth_headers,
        params={
            "booking_date": "not-a-date"
        },
    )

    assert response.status_code == 422