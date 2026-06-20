from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ugc_video_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.render_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    task_soft_time_limit=540,  # 9 minutes
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
)