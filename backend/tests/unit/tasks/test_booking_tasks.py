from unittest.mock import AsyncMock, patch


def test_send_booking_reminder_task():
    with patch(
        "src.tasks.booking_tasks._send_booking_reminders",
        new_callable=AsyncMock,
    ) as send_reminders:

        from src.tasks.booking_tasks import (
            send_booking_reminder,
        )

        send_booking_reminder()

    send_reminders.assert_awaited_once()