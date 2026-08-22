from unittest.mock import AsyncMock, patch

import pytest

from src.bookings.models import BookingStatus
from src.bookings.reminder_service import (
    BookingReminderService,
)


@pytest.mark.anyio
async def test_send_reminders():
    booking = type(
        "BookingMock",
        (),
        {
            "id": "booking-id",
            "client_email": "user@example.com",
            "reminder_sent": False,
            "status": BookingStatus.CONFIRMED,
        },
    )()

    repository = AsyncMock()

    repository.get_bookings_for_reminder = AsyncMock(
        return_value=[
            booking,
        ]
    )

    repository.update = AsyncMock()

    service = BookingReminderService(
        booking_repository=repository,
    )

    with patch(
        "src.bookings.reminder_service."
        "send_booking_reminder_email.delay"
    ) as send_email:

        await service.send_reminders()

    send_email.assert_called_once_with(
        "user@example.com",
        "booking-id",
    )

    assert booking.reminder_sent is True

    repository.update.assert_awaited_once_with(
        booking
    )

@pytest.mark.anyio
async def test_send_reminders_without_email():
    booking = type(
        "BookingMock",
        (),
        {
            "id": "booking-id",
            "client_email": None,
            "reminder_sent": False,
            "status": BookingStatus.CONFIRMED,
        },
    )()

    repository = AsyncMock()

    repository.get_bookings_for_reminder = AsyncMock(
        return_value=[
            booking,
        ]
    )

    repository.update = AsyncMock()

    service = BookingReminderService(
        booking_repository=repository,
    )

    with patch(
        "src.bookings.reminder_service."
        "send_booking_reminder_email.delay"
    ) as send_email:

        await service.send_reminders()

    send_email.assert_not_called()

    assert booking.reminder_sent is False

    repository.update.assert_not_awaited()