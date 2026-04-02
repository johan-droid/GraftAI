import os
import asyncio
import logging
from arq import create_pool
from arq.connections import RedisSettings
from dotenv import load_dotenv

# Load env before any local imports
load_dotenv()

# Initialize Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import background-capable services
from backend.services.notifications import notify_welcome_email
from backend.services.sync_engine import sync_user_calendar

async def startup(ctx):
    """
    Worker initialization.
    Add any state (like DB engines or shared clients) to the context here.
    """
    logger.info("🚀 GraftAI Background Worker Starting...")
    from backend.utils.db import AsyncSessionLocal
    ctx['db_session_factory'] = AsyncSessionLocal

async def shutdown(ctx):
    """Worker cleanup."""
    logger.info("🛑 GraftAI Background Worker Shutting Down...")

# Job Wrappers (to handle DB session lifecycle)
async def task_notify_welcome(ctx, user_email: str, full_name: str):
    logger.info(f"📧 Sending background welcome email to {user_email}")
    # notifications already handles its own logic, we just wrapper it
    await notify_welcome_email(user_email, full_name)

async def task_sync_calendar(ctx, user_id: str):
    logger.info(f"🔄 Processing background sync for user {user_id}")
    async with ctx['db_session_factory']() as db:
        await sync_user_calendar(db, user_id)

class WorkerSettings:
    """Settings for the arq worker."""
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    functions = [task_notify_welcome, task_sync_calendar]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    job_timeout = 300 # 5 minutes for heavy syncs
