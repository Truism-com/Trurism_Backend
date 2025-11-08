"""
Minimal Celery app for background tasks.

This module exposes `celery_app` which can be used by workers:

    celery -A app.celery.celery_app worker --loglevel=info

Add broker/result backend URLs via environment or `.env` using
`CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` (these map to
`settings.celery_broker_url` and `settings.celery_result_backend`).
"""
from celery import Celery
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Use settings if provided, otherwise empty strings
broker = settings.celery_broker_url or None
backend = settings.celery_result_backend or None

celery_app = Celery(
    "app",
    broker=broker,
    backend=backend,
)

# Example configuration (can be overridden in production)
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(bind=True)
def debug_task(self, info=None):
    logger.info(f"Running debug_task; info={info}")
    return {"status": "ok", "info": info}
