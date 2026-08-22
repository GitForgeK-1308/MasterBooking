from datetime import datetime, timedelta

from src.bookings.models import Booking
from src.bookings.repository import BookingRepository
from src.tasks.email_tasks import send_booking_reminder_email


class BookingReminderService:
    def __init__(
        self,
        booking_repository: BookingRepository,
    ) -> None:
        self.booking_repository = booking_repository

    async def send_reminders(self) -> None:
        target_datetime = (
            datetime.now()
            + timedelta(hours=1)
        ).replace(
            second=0,
            microsecond=0,
        )

        bookings = await (
            self.booking_repository
            .get_bookings_for_reminder(
                target_datetime
            )
        )

        for booking in bookings:
            await self._send_reminder(
                booking
            )

    async def _send_reminder(
        self,
        booking: Booking,
    ) -> None:
        if booking.client_email is None:
            return

        send_booking_reminder_email.delay(
            booking.client_email,
            str(booking.id),
        )

        booking.reminder_sent = True

        await self.booking_repository.update(
            booking
        )