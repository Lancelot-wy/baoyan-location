"""Celery application configuration."""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "baoyan",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.ingestion_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
