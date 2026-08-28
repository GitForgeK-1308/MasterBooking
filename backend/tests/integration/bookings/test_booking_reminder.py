from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.models import Booking
from src.bookings.reminder_service import (
    BookingReminderService,
)
from src.bookings.repository import (
    BookingRepository,
)


@pytest.mark.anyio
async def test_booking_reminder_marks_booking_as_sent(
    db_session: AsyncSession,
    reminder_booking: Booking,
):
    repository = BookingRepository(db_session)

    service = BookingReminderService(
        booking_repository=repository,
    )

    reminder_booking.client_email = "client@example.com"
    reminder_booking.reminder_sent = False

    await db_session.commit()

    with patch(
        "src.bookings.reminder_service.send_booking_reminder_email.delay"
    ) as send_email:
        await service.send_reminders()

    send_email.assert_called_once()

    await db_session.refresh(reminder_booking)

    assert reminder_booking.reminder_sent is True
