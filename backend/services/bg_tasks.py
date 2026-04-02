import os
import logging

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
