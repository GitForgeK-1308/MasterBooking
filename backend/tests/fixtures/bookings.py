from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.password import hash_password
from src.auth.token import create_access_token
from src.bookings.models import (
    Booking,
    BookingStatus,
)
from src.master_offering.models import MasterOffering
from src.master_schedule.models import (
    MasterSchedule,
    WeekDay,
)
from src.masters.models import Master
from src.users.models import User

TEST_BOOKING_USER_PASSWORD = "StrongPassword123!"


def get_next_weekday(
    weekday: int,
) -> date:
    today = date.today()

    days_ahead = (
        weekday - today.weekday()
    ) % 7

    if days_ahead == 0:
        days_ahead = 7

    return today + timedelta(
        days=days_ahead
    )


@pytest.fixture
def future_booking_date() -> date:
    return get_next_weekday(
        0
    )


@pytest.fixture
async def no_phone_user(
    db_session: AsyncSession,
) -> User:
    user = User(
        email="no-phone@example.com",
        hashed_password=hash_password(
            TEST_BOOKING_USER_PASSWORD
        ),
        first_name="No",
        last_name="Phone",
        phone=None,
        is_active=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
def no_phone_auth_headers(
    no_phone_user: User,
) -> dict[str, str]:
    token = create_access_token(
        user_id=no_phone_user.id
    )

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
async def second_booking_user(
    db_session: AsyncSession,
) -> User:
    user = User(
        email="second-client@example.com",
        hashed_password=hash_password(
            TEST_BOOKING_USER_PASSWORD
        ),
        first_name="Pavel",
        last_name="Smirnov",
        phone="+79990000002",
        is_active=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
def second_booking_auth_headers(
    second_booking_user: User,
) -> dict[str, str]:
    token = create_access_token(
        user_id=second_booking_user.id
    )

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
async def booking_schedule(
    db_session: AsyncSession,
    master: Master,
) -> MasterSchedule:
    schedule = MasterSchedule(
        master_id=master.id,
        day_of_week=WeekDay.MONDAY,
        start_time=time(
            9,
            0,
        ),
        end_time=time(
            17,
            0,
        ),
        is_working=True,
    )

    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(
        schedule
    )

    return schedule


@pytest.fixture
async def booking(
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
            10,
            0,
        ),
        end_time=time(
            11,
            0,
        ),
        client_name=(
            f"{user.first_name} "
            f"{user.last_name}"
        ),
        client_phone=user.phone,
        client_email=user.email,
        status=BookingStatus.PENDING,
    )

    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(
        booking
    )

    return booking


@pytest.fixture
async def second_booking(
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
            12,
            0,
        ),
        end_time=time(
            13,
            0,
        ),
        client_name=(
            f"{user.first_name} "
            f"{user.last_name}"
        ),
        client_phone=user.phone,
        client_email=user.email,
        status=BookingStatus.CONFIRMED,
    )

    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(
        booking
    )

    return booking


@pytest.fixture
async def foreign_booking(
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
            14,
            0,
        ),
        end_time=time(
            15,
            0,
        ),
        client_name=(
            f"{second_booking_user.first_name} "
            f"{second_booking_user.last_name}"
        ),
        client_phone=second_booking_user.phone,
        client_email=second_booking_user.email,
        status=BookingStatus.PENDING,
    )

    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(
        booking
    )

    return booking


@pytest.fixture
async def reminder_booking(
    db_session: AsyncSession,
    user: User,
    master: Master,
    offering: MasterOffering,
) -> Booking:
    reminder_time = (
        datetime.now()
        + timedelta(hours=1)
    ).replace(
        second=0,
        microsecond=0,
    )

    booking = Booking(
        client_id=user.id,
        master_id=master.id,
        offering_id=offering.id,
        booking_date=reminder_time.date(),
        start_time=reminder_time.time(),
        end_time=(
            reminder_time
            + timedelta(minutes=60)
        ).time(),
        client_name=(
            f"{user.first_name} "
            f"{user.last_name}"
        ),
        client_phone=user.phone,
        client_email=user.email,
        status=BookingStatus.CONFIRMED,
        reminder_sent=False,
    )

    db_session.add(booking)

    await db_session.commit()
    await db_session.refresh(
        booking
    )

    return booking