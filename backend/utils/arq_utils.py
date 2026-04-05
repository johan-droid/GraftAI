import os
import logging
from arq.connections import RedisSettings, create_pool

logger = logging.getLogger(__name__)

_redis_pool = None

async def get_arq_pool():
    """Returns a singleton arq pool for enqueuing background jobs."""
    global _redis_pool
    if _redis_pool is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            _redis_pool = await create_pool(RedisSettings.from_dsn(redis_url))
            logger.info("✅ arq Redis pool successfully initialized.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize arq Redis pool: {e}")
            return None
    return _redis_pool

async def enqueue_job(function_name: str, **kwargs):
    """Safely enqueues a job without crashing if Redis is down."""
    pool = await get_arq_pool()
    if not pool:
        logger.warning(f"⚠ Skipping background job {function_name}: no Redis pool available.")
        return None
    try:
        job = await pool.enqueue_job(function_name, **kwargs)
        logger.info(f"📤 Enqueued background job: {function_name} (ID: {job.job_id})")
        return job
    except Exception as e:
        logger.error(f"❌ Failed to enqueue job {function_name}: {e}")
        return None
