"""
Celery configuration for background job processing.
Handles: email sending, calendar sync, webhook delivery, reminders
"""

import os

try:
    from celery import Celery
    from celery.signals import task_prerun, task_postrun

    _CELERY_AVAILABLE = True
except ImportError:
    _CELERY_AVAILABLE = False

    class DummyTask:
        def __init__(self, fn):
            self.fn = fn

        def __call__(self, *args, **kwargs):
            return self.fn(*args, **kwargs)

        def delay(self, *args, **kwargs):
            try:
                return self.fn(*args, **kwargs)
            except TypeError:
                return self.fn(None, *args, **kwargs)

        def apply_async(self, *args, **kwargs):
            return self.delay(*args, **kwargs)

    class DummyConfig(dict):
        def update(self, *args, **kwargs):
            super().update(*args, **kwargs)

        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name)

        def __setattr__(self, name, value):
            self[name] = value

    class DummyCelery:
        def __init__(self, *args, **kwargs):
            self.conf = DummyConfig()

        def task(self, *task_args, **task_kwargs):
            def decorator(fn):
                return DummyTask(fn)

            return decorator

    class DummySignal:
        def connect(self, *args, **kwargs):
            return None

    Celery = DummyCelery
    task_prerun = DummySignal()
    task_postrun = DummySignal()

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "graftai",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "backend.tasks.email_tasks",
        "backend.tasks.calendar_tasks",
        "backend.tasks.webhook_tasks",
        "backend.tasks.workflow_tasks",
        "backend.tasks.reminder_tasks",
    ],
)

# Celery settings
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    # Result backend
    result_expires=3600,  # 1 hour
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Queue settings
    task_default_queue="default",
    task_routes={
        "backend.tasks.email_tasks.*": {"queue": "email"},
        "backend.tasks.calendar_tasks.*": {"queue": "calendar"},
        "backend.tasks.webhook_tasks.*": {"queue": "webhook"},
        "backend.tasks.workflow_tasks.*": {"queue": "workflow"},
        "backend.tasks.reminder_tasks.*": {"queue": "reminder"},
    },
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
)


@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **extras):
    """Log task start."""
    logger.info(f"Starting task {task.name}[{task_id}]")


@task_postrun.connect
def task_postrun_handler(task_id, task, args, kwargs, retval, state, **extras):
    """Log task completion."""
    logger.info(f"Task {task.name}[{task_id}] finished with state: {state}")


# Beat schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    # Calendar sync every 5 minutes
    "sync-calendars": {
        "task": "backend.tasks.calendar_tasks.sync_all_calendars",
        "schedule": 300.0,  # 5 minutes
    },
    # Send pending reminders every minute
    "send-reminders": {
        "task": "backend.tasks.reminder_tasks.send_pending_reminders",
        "schedule": 60.0,  # 1 minute
    },
    # Process scheduled workflows every minute
    "process-workflows": {
        "task": "backend.tasks.workflow_tasks.process_scheduled_workflows",
        "schedule": 60.0,  # 1 minute
    },
    # Retry failed webhooks every 5 minutes
    "retry-webhooks": {
        "task": "backend.tasks.webhook_tasks.retry_failed_webhooks",
        "schedule": 300.0,  # 5 minutes
    },
}


if __name__ == "__main__":
    celery_app.start()
