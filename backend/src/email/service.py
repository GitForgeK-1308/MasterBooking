import smtplib
from email.message import EmailMessage

from src.config import settings


class EmailService:
    def send_password_reset_email(
        self,
        email: str,
        token: str,
    ) -> None:
        reset_url = (
            f"{settings.frontend_reset_password_url}"
            f"?token={token}"
        )

        message = EmailMessage()

        message["Subject"] = (
            "Восстановление пароля MasterBooking"
        )
        message["From"] = settings.smtp_from_email
        message["To"] = email

        message.set_content(
            (
                "Для восстановления пароля "
                "перейдите по ссылке:\n\n"
                f"{reset_url}\n\n"
                "Ссылка действует 15 минут."
            )
        )

        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
        ) as smtp:
            smtp.starttls()
            smtp.login(
                settings.smtp_user,
                settings.smtp_password,
            )
            smtp.send_message(
                message
            )