import uuid
from datetime import (
    date,
    datetime,
    timedelta,
)

import pytest

from src.bookings.models import (
    Booking,
    BookingStatus,
)
from src.bookings.repository import (
    BookingRepository,
)


@pytest.mark.anyio
async def test_get_bookings_for_reminder(
    db_session,
    master,
    offering,
):
    start_time = (
        datetime.now()
        + timedelta(hours=1)
    ).replace(
        microsecond=0,
        second=0,
    ).time()

    booking = Booking(
        id=uuid.uuid4(),
        master_id=master.id,
        offering_id=offering.id,
        booking_date=date.today(),
        start_time=start_time,
        end_time=(
            datetime.combine(
                date.today(),
                start_time,
            )
            + timedelta(minutes=30)
        ).time(),
        client_name="Test Client",
        client_phone="+79999999999",
        client_email="test@example.com",
        status=BookingStatus.CONFIRMED,
        reminder_sent=False,
    )

    db_session.add(booking)
    await db_session.commit()

    repository = BookingRepository(
        db_session
    )

    bookings = await repository.get_bookings_for_reminder(
        datetime.combine(
            date.today(),
            start_time,
        )
    )

    assert len(bookings) == 1
    assert bookings[0].id == booking.id