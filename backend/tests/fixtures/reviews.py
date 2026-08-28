from datetime import (
    date,
    datetime,
    time,
    timezone,
)

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.models import (
    Booking,
    BookingStatus,
)
from src.master_offering.models import MasterOffering
from src.masters.models import Master
from src.reviews.models import Review
from src.users.models import User


@pytest.fixture
async def completed_booking(
    db_session: AsyncSession,
    user: User,
    master: Master,
    offering: MasterOffering,
    future_booking_date: date,
) -> Booking:
    booking = Booking(
        client_id=user.id,
        master_id=master.id,
        offering_id=offering.id,
        booking_date=future_booking_date,
        start_time=time(
            15,
            0,
        ),
        end_time=time(
            16,
            0,
        ),
        client_name=(f"{user.first_name} {user.last_name}"),
        client_phone=user.phone,
        client_email=user.email,
        status=BookingStatus.COMPLETED,
    )

    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)

    return booking


@pytest.fixture
async def second_completed_booking(
    db_session: AsyncSession,
    user: User,
    master: Master,
    offering: MasterOffering,
    future_booking_date: date,
) -> Booking:
    booking = Booking(
        client_id=user.id,
        master_id=master.id,
        offering_id=offering.id,
        booking_date=future_booking_date,
        start_time=time(
            16,
            0,
        ),
        end_time=time(
            17,
            0,
        ),
        client_name=(f"{user.first_name} {user.last_name}"),
        client_phone=user.phone,
        client_email=user.email,
        status=BookingStatus.COMPLETED,
    )

    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)

    return booking


@pytest.fixture
async def foreign_completed_booking(
    db_session: AsyncSession,
    second_booking_user: User,
    master: Master,
    offering: MasterOffering,
    future_booking_date: date,
) -> Booking:
    booking = Booking(
        client_id=second_booking_user.id,
        master_id=master.id,
        offering_id=offering.id,
        booking_date=future_booking_date,
        start_time=time(
            13,
            0,
        ),
        end_time=time(
            14,
            0,
        ),
        client_name=(
            f"{second_booking_user.first_name} {second_booking_user.last_name}"
        ),
        client_phone=second_booking_user.phone,
        client_email=second_booking_user.email,
        status=BookingStatus.COMPLETED,
    )

    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)

    return booking


@pytest.fixture
async def review(
    db_session: AsyncSession,
    user: User,
    master: Master,
    completed_booking: Booking,
) -> Review:
    review = Review(
        booking_id=completed_booking.id,
        master_id=master.id,
        client_id=user.id,
        rating=5,
        comment="Отличная работа!",
        created_at=datetime(
            2026,
            8,
            10,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)

    return review


@pytest.fixture
async def second_review(
    db_session: AsyncSession,
    user: User,
    master: Master,
    second_completed_booking: Booking,
) -> Review:
    review = Review(
        booking_id=second_completed_booking.id,
        master_id=master.id,
        client_id=user.id,
        rating=4,
        comment="Всё понравилось.",
        created_at=datetime(
            2026,
            8,
            11,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)

    return review


@pytest.fixture
async def deleted_user_review(
    db_session: AsyncSession,
    master: Master,
    foreign_completed_booking: Booking,
) -> Review:
    review = Review(
        booking_id=foreign_completed_booking.id,
        master_id=master.id,
        client_id=None,
        rating=3,
        comment="Нормально.",
        created_at=datetime(
            2026,
            8,
            12,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)

    return review


@pytest.fixture
async def foreign_master_review(
    db_session: AsyncSession,
    second_booking_user: User,
    second_master: Master,
    second_master_offering: MasterOffering,
    future_booking_date: date,
) -> Review:
    booking = Booking(
        client_id=second_booking_user.id,
        master_id=second_master.id,
        offering_id=second_master_offering.id,
        booking_date=future_booking_date,
        start_time=time(
            10,
            0,
        ),
        end_time=time(
            11,
            30,
        ),
        client_name=(
            f"{second_booking_user.first_name} {second_booking_user.last_name}"
        ),
        client_phone=second_booking_user.phone,
        client_email=second_booking_user.email,
        status=BookingStatus.COMPLETED,
    )

    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)

    review = Review(
        booking_id=booking.id,
        master_id=second_master.id,
        client_id=second_booking_user.id,
        rating=2,
        comment="Можно лучше.",
        created_at=datetime(
            2026,
            8,
            13,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)

    return review
