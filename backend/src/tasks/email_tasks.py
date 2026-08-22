import logging

from src.email.service import EmailService
from src.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def send_password_reset_email(
    email: str,
    token: str,
) -> None:
    email_service = EmailService()

    email_service.send_password_reset_email(
        email=email,
        token=token,
    )


@celery_app.task
def send_booking_reminder_email(
    email: str,
    booking_id: str,
) -> None:
    email_service = EmailService()

    email_service.send_booking_reminder_email(
        email=email,
        booking_id=booking_id,
    )