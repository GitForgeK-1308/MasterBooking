from celery import Celery

from src.config import settings

celery_app = Celery(
    "masterbooking",
    broker=settings.celery_broker_url,
    include=[
        "src.tasks.email_tasks",
         "src.tasks.booking_tasks",
    ],
)

celery_app.conf.beat_schedule = {
    "send-booking-reminder-every-minute": {
        "task": "src.tasks.booking_tasks.send_booking_reminder",
        "schedule": 60.0,
    },
}