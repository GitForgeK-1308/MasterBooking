from email.message import EmailMessage
from unittest.mock import MagicMock, patch

from src.email.service import EmailService


def test_send_password_reset_email():
    service = EmailService()

    smtp_mock = MagicMock()
    smtp_context = MagicMock()
    smtp_context.__enter__.return_value = smtp_mock

    with patch(
        "src.email.service.smtplib.SMTP",
        return_value=smtp_context,
    ):
        service.send_password_reset_email(
            email="user@example.com",
            token="test-token",
        )

    smtp_mock.starttls.assert_called_once()

    smtp_mock.login.assert_called_once()

    smtp_mock.send_message.assert_called_once()


def test_password_reset_email_contains_reset_url():
    service = EmailService()

    smtp_mock = MagicMock()
    smtp_context = MagicMock()
    smtp_context.__enter__.return_value = smtp_mock

    with patch(
        "src.email.service.smtplib.SMTP",
        return_value=smtp_context,
    ):
        service.send_password_reset_email(
            email="user@example.com",
            token="test-token",
        )

    message = smtp_mock.send_message.call_args.args[0]

    assert isinstance(
        message,
        EmailMessage,
    )

    body = message.get_content()

    assert "http://localhost:3000/reset-password?token=test-token" in body

    assert message["To"] == "user@example.com"
