from unittest.mock import MagicMock, patch

from src.tasks.email_tasks import (
    send_password_reset_email,
)


def test_send_password_reset_email_task():
    email_service = MagicMock()

    with patch(
        "src.tasks.email_tasks.EmailService",
        return_value=email_service,
    ):
        send_password_reset_email.run(
            email="user@example.com",
            token="test-token",
        )

    email_service.send_password_reset_email.assert_called_once_with(
        email="user@example.com",
        token="test-token",
    )