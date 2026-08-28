import uuid
from datetime import date, time, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.models import (
    Booking,
    BookingStatus,
)
from src.bookings.repository import BookingRepository
from src.master_offering.models import MasterOffering
from src.masters.models import Master
from src.users.models import User


def make_booking(
    *,
    client_id: uuid.UUID,
    master_id: uuid.UUID,
    offering_id: uuid.UUID,
    booking_date: date,
    start_time: time,
    end_time: time,
    status: BookingStatus = BookingStatus.PENDING,
) -> Booking:
    return Booking(
        client_id=client_id,
        master_id=master_id,
        offering_id=offering_id,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        client_name="Test Client",
        client_phone="+79990000000",
        client_email="client@example.com",
        status=status,
    )


@pytest.mark.anyio
async def test_create_booking(
    db_session: AsyncSession,
    user: User,
    master: Master,
    offering: MasterOffering,
    future_booking_date: date,
):
    repository = BookingRepository(db_session)

    booking = make_booking(
        client_id=user.id,
        master_id=master.id,
        offering_id=offering.id,
        booking_date=future_booking_date,
        start_time=time(
            9,
            0,
        ),
        end_time=time(
            10,
            0,
        ),
    )

    result = await repository.create(booking)

    assert result.id is not None
    assert isinstance(
        result.id,
        uuid.UUID,
    )

    assert result.client_id == user.id
    assert result.master_id == master.id
    assert result.offering_id == offering.id

    assert result.booking_date == future_booking_date

    assert result.start_time == time(
        9,
        0,
    )

    assert result.end_time == time(
        10,
        0,
    )

    assert result.status == BookingStatus.PENDING

    assert result.created_at is not None


@pytest.mark.anyio
async def test_get_booking_by_id(
    db_session: AsyncSession,
    booking: Booking,
):
    repository = BookingRepository(db_session)

    booking_id = booking.id

    db_session.expunge(booking)

    result = await repository.get_by_id(booking_id)

    assert result is not None
    assert result.id == booking_id

    assert result.status == BookingStatus.PENDING


@pytest.mark.anyio
async def test_get_booking_by_id_not_found(
    db_session: AsyncSession,
):
    repository = BookingRepository(db_session)

    result = await repository.get_by_id(uuid.uuid4())

    assert result is None


@pytest.mark.anyio
async def test_get_by_master_and_date_sorted_and_scoped(
    db_session: AsyncSession,
    user: User,
    master: Master,
    second_master: Master,
    second_master_offering: MasterOffering,
    booking: Booking,
    second_booking: Booking,
    foreign_booking: Booking,
    future_booking_date: date,
):
    repository = BookingRepository(db_session)

    other_master_booking = make_booking(
        client_id=user.id,
        master_id=second_master.id,
        offering_id=second_master_offering.id,
        booking_date=future_booking_date,
        start_time=time(
            9,
            0,
        ),
        end_time=time(
            10,
            0,
        ),
    )

    await repository.create(other_master_booking)

    result = await repository.get_by_master_and_date(
        master_id=master.id,
        booking_date=future_booking_date,
    )

    assert [item.id for item in result] == [
        booking.id,
        second_booking.id,
        foreign_booking.id,
    ]

    assert all(item.master_id == master.id for item in result)

    assert other_master_booking.id not in {item.id for item in result}


@pytest.mark.anyio
async def test_get_by_master_and_date_empty(
    db_session: AsyncSession,
    master: Master,
    future_booking_date: date,
):
    repository = BookingRepository(db_session)

    result = await repository.get_by_master_and_date(
        master_id=master.id,
        booking_date=(future_booking_date + timedelta(days=1)),
    )

    assert result == []


@pytest.mark.anyio
async def test_get_active_by_master_and_date_excludes_cancelled(
    db_session: AsyncSession,
    master: Master,
    booking: Booking,
    second_booking: Booking,
    foreign_booking: Booking,
    future_booking_date: date,
):
    repository = BookingRepository(db_session)

    second_booking.status = BookingStatus.CANCELLED

    foreign_booking.status = BookingStatus.COMPLETED

    await db_session.commit()

    result = await repository.get_active_by_master_and_date(
        master_id=master.id,
        booking_date=future_booking_date,
    )

    assert [item.id for item in result] == [
        booking.id,
        foreign_booking.id,
    ]

    assert second_booking.id not in {item.id for item in result}


@pytest.mark.anyio
async def test_get_conflicting_booking(
    db_session: AsyncSession,
    master: Master,
    booking: Booking,
    future_booking_date: date,
):
    repository = BookingRepository(db_session)

    result = await repository.get_conflicting_booking(
        master_id=master.id,
        booking_date=future_booking_date,
        start_time=time(
            10,
            30,
        ),
        end_time=time(
            11,
            30,
        ),
    )

    assert result is not None
    assert result.id == booking.id


@pytest.mark.anyio
async def test_adjacent_booking_does_not_conflict(
    db_session: AsyncSession,
    master: Master,
    booking: Booking,
    future_booking_date: date,
):
    repository = BookingRepository(db_session)

    result = await repository.get_conflicting_booking(
        master_id=master.id,
        booking_date=future_booking_date,
        start_time=time(
            11,
            0,
        ),
        end_time=time(
            12,
            0,
        ),
    )

    assert result is None


@pytest.mark.anyio
async def test_cancelled_booking_does_not_conflict(
    db_session: AsyncSession,
    master: Master,
    booking: Booking,
    future_booking_date: date,
):
    repository = BookingRepository(db_session)

    booking.status = BookingStatus.CANCELLED

    await db_session.commit()

    result = await repository.get_conflicting_booking(
        master_id=master.id,
        booking_date=future_booking_date,
        start_time=time(
            10,
            30,
        ),
        end_time=time(
            11,
            30,
        ),
    )

    assert result is None


@pytest.mark.anyio
async def test_get_by_client_id_sorted_and_scoped(
    db_session: AsyncSession,
    user: User,
    booking: Booking,
    second_booking: Booking,
    foreign_booking: Booking,
):
    repository = BookingRepository(db_session)

    result = await repository.get_by_client_id(user.id)

    assert [item.id for item in result] == [
        booking.id,
        second_booking.id,
    ]

    assert all(item.client_id == user.id for item in result)

    assert foreign_booking.id not in {item.id for item in result}


@pytest.mark.anyio
async def test_get_by_client_id_empty(
    db_session: AsyncSession,
    second_booking_user: User,
):
    repository = BookingRepository(db_session)

    result = await repository.get_by_client_id(second_booking_user.id)

    assert result == []


@pytest.mark.anyio
async def test_update_booking_status(
    db_session: AsyncSession,
    booking: Booking,
):
    repository = BookingRepository(db_session)

    booking.status = BookingStatus.CONFIRMED

    result = await repository.update(booking)

    assert result.status == BookingStatus.CONFIRMED

    booking_id = result.id

    db_session.expunge(result)

    booking_from_database = await repository.get_by_id(booking_id)

    assert booking_from_database is not None

    assert booking_from_database.status == BookingStatus.CONFIRMED
