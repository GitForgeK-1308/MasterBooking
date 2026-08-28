import asyncio

from src.bookings.reminder_service import (
    BookingReminderService,
)
from src.bookings.repository import (
    BookingRepository,
)
from src.database.session import (
    get_celery_session,
)
from src.tasks.celery_app import celery_app


async def _send_booking_reminders() -> None:
    async with get_celery_session() as session:
        repository = BookingRepository(session)

        service = BookingReminderService(
            booking_repository=repository,
        )

        await service.send_reminders()


@celery_app.task
def send_booking_reminder() -> None:
    asyncio.run(_send_booking_reminders())
