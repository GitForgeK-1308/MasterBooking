from celery import Celery

from src.config import settings


celery_app = Celery(
    "masterbooking",
    broker=settings.celery_broker_url,
)