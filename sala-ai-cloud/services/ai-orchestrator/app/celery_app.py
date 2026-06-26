from celery import Celery

from app.config import settings

celery = Celery(
    "sedapps_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workflows.site_generation",
        "app.workflows.article_generation",
    ],
)

celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_default_queue="ai",
    task_soft_time_limit=1800,
    task_time_limit=2700,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
)
