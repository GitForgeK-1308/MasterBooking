import logging

from src.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def send_password_reset_email(
    email: str,
    token: str,
) -> None:
    logger.info(
        "Запрошена отправка письма восстановления пароля для %s",
        email,
    )