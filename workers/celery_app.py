from celery import Celery
from config.settings import settings

celery_app = Celery(
    "omni_agent_saas",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=["workers.sheet_worker", "workers.email_worker"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
