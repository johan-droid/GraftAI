import os
import logging
from typing import Optional

try:
    from arq import create_pool
    from arq.connections import RedisSettings
except ModuleNotFoundError:
    create_pool = None
    RedisSettings = None

logger = logging.getLogger(__name__)

# Shared pool for task enqueuing
_arq_pool = None

async def get_task_pool():
    """Returns the shared Arq Redis pool for enqueuing tasks."""
    if create_pool is None or RedisSettings is None:
        raise RuntimeError("arq is not installed")

    global _arq_pool
    if _arq_pool is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _arq_pool = await create_pool(RedisSettings.from_dsn(redis_url))
        logger.info("⚡ Arq Task Pool initialized")
    return _arq_pool

async def enqueue_welcome_email(user_email: str, full_name: str):
    """Enqueue a welcome email task."""
    pool = await get_task_pool()
    await pool.enqueue_job('task_notify_welcome', user_email, full_name)
    logger.info(f"✅ Enqueued welcome email for {user_email}")

async def enqueue_calendar_sync(user_id: str):
    """Enqueue a calendar sync task."""
    pool = await get_task_pool()
    await pool.enqueue_job('task_sync_calendar', user_id)
    logger.info(f"✅ Enqueued calendar sync for user {user_id}")

async def enqueue_event_confirmation(email: str, event_title: str, event_time: str, meeting_link: Optional[str] = None):
    """Enqueue a meeting confirmation email."""
    pool = await get_task_pool()
    await pool.enqueue_job('task_notify_event', email, 'confirmation.html', 'Meeting Confirmed - GraftAI', {
        'event_title': event_title,
        'event_time': event_time,
        'meeting_link': meeting_link
    })

async def enqueue_event_update(email: str, event_title: str, event_time: str, meeting_link: Optional[str] = None):
    """Enqueue a meeting update email."""
    pool = await get_task_pool()
    await pool.enqueue_job('task_notify_event', email, 'update.html', 'Update: Meeting Details Changed - GraftAI', {
        'event_title': event_title,
        'event_time': event_time,
        'meeting_link': meeting_link
    })

async def enqueue_event_cancellation(email: str, event_title: str, event_time: str):
    """Enqueue a meeting cancellation email."""
    pool = await get_task_pool()
    await pool.enqueue_job('task_notify_event', email, 'cancellation.html', 'Cancelled: Meeting Removed - GraftAI', {
        'event_title': event_title,
        'event_time': event_time
    })

async def enqueue_account_deletion(email: str):
    """Enqueue an account deletion 'Goodbye' email."""
    pool = await get_task_pool()
    await pool.enqueue_job('task_notify_event', email, 'goodbye.html', 'Account Successfully Deleted - GraftAI', {})

async def enqueue_sync_error_alert(email: str, error_message: str):
    """Enqueue a calendar sync error alert."""
    pool = await get_task_pool()
    await pool.enqueue_job('task_notify_event', email, 'sync_error.html', 'Action Required: Calendar Sync Failed - GraftAI', {
        'error_message': error_message
    })

async def enqueue_conflict_alert(email: str, requested_event: str, existing_event: str):
    """Enqueue a scheduling conflict alert."""
    pool = await get_task_pool()
    await pool.enqueue_job('task_notify_event', email, 'conflict_alert.html', 'Schedule Conflict Alert - GraftAI', {
        'requested_event': requested_event,
        'existing_event': existing_event
    })
