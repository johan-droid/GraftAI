import os
import logging
from arq.connections import RedisSettings
from dotenv import load_dotenv

# Load env before any local imports
load_dotenv()

# Initialize Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import background-capable services
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_
from backend.models.tables import EventTable, UserTable
from backend.services.notifications import notify_welcome_email, notify_event_reminder
from backend.services.sync_engine import sync_user_calendar

async def task_process_event_reminders(ctx):
    """
    Periodic task to check for upcoming events and send reminders.
    Runs every minute but only processes events starting in the next 15-20 mins.
    """
    logger.info("[WORKER] 🔔 Checking for upcoming event reminders...")
    async with ctx['db_session_factory']() as db:
        now = datetime.now(timezone.utc)
        reminder_window = now + timedelta(minutes=20)
        
        # Query events starting soon that haven't been reminded yet
        stmt = (
            select(EventTable, UserTable.email, UserTable.full_name)
            .join(UserTable, EventTable.user_id == UserTable.id)
            .where(
                and_(
                    EventTable.start_time <= reminder_window,
                    EventTable.start_time > now,
                    EventTable.is_reminded == False,
                    EventTable.status == "confirmed"
                )
            )
        )
        result = await db.execute(stmt)
        rows = result.all()
        
        for event, user_email, user_name in rows:
            try:
                # Prepare event data for the notification service
                event_data = {
                    "id": event.id,
                    "user_id": event.user_id,
                    "title": event.title,
                    "start_time": event.start_time.strftime("%I:%M %p"),
                    "end_time": event.end_time.strftime("%I:%M %p"),
                    "is_meeting": event.is_meeting,
                    "meeting_platform": event.meeting_platform,
                    "meeting_link": event.meeting_link,
                    "full_name": user_name
                }
                
                await notify_event_reminder(user_email, [], event_data)
                
                # Mark as reminded
                event.is_reminded = True
                logger.info(f"[WORKER] 🔔 Reminder sent for event '{event.title}' to {user_email}")
            except Exception as e:
                logger.error(f"[WORKER] ❌ Failed to send reminder for event {event.id}: {e}")
        
        await db.commit()

async def task_background_ai_sync(ctx, event_id: int, user_id: str, action: str = "upsert"):
    """
    Worker task to perform Pinecone operations in the background.
    Action can be 'upsert' or 'delete'.
    """
    from backend.services.ai_sync import sync_event_to_vector_store, purge_event_from_vector_store
    
    if action == "delete":
        logger.info(f"[WORKER] 🗑 AI Sync: Purging event {event_id} (user: {user_id})")
        await purge_event_from_vector_store(event_id, user_id)
        return

    logger.info(f"[WORKER] 🧠 AI Sync: Indexing context for event {event_id} (user: {user_id})")
    async with ctx['db_session_factory']() as db:
        stmt = select(EventTable).where(EventTable.id == event_id)
        result = await db.execute(stmt)
        event = result.scalars().first()
        
        if not event:
            logger.warning(f"[WORKER] ⚠️ Skipping AI sync: event {event_id} not found in database.")
            return
            
        await sync_event_to_vector_store(event)

async def task_renew_webhooks(ctx):
    """
    Periodic task to renew Google and Microsoft push notification subscriptions.
    Ensures 'Perfect Sync' remains active by refreshing tokens before they expire.
    """
    from backend.services.integrations.webhook_manager import renew_all_expiring_subscriptions
    logger.info("[WORKER] ♻️ Periodic Sync: Checking for expiring webhook subscriptions...")
    async with ctx['db_session_factory']() as db:
        await renew_all_expiring_subscriptions(db)
    logger.info("♻️ Checking for expiring webhook subscriptions...")
    async with ctx['db_session_factory']() as db:
        await renew_all_expiring_subscriptions(db)

async def startup(ctx):
    """
    Initializes shared resources (DB and Monitoring) for the background worker.
    Ensures Sentry observability is active for all jobs.
    """
    from backend.utils.db import get_async_session_factory
    ctx['db_session_factory'] = get_async_session_factory()
    
    # Initialize Sentry for Worker (if DSN provided)
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        import sentry_sdk
        try:
            sentry_sdk.init(
                dsn=sentry_dsn,
                traces_sample_rate=0.1,
                environment=os.getenv("ENV", "production"),
            )
            logger.info("[WORKER] ✅ Sentry monitoring active.")
        except Exception as e:
            logger.error(f"[WORKER] ❌ Sentry initialization failed: {e}")
    
    logger.info("[WORKER] 🚀 Background worker started.")

async def shutdown(ctx):
    """Cleanly closes resources upon worker termination."""
    logger.info("[WORKER] 🛑 Background worker shutting down.")

class WorkerSettings:
    """Settings for the arq worker."""
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    functions = [
        task_notify_welcome, 
        task_sync_calendar, 
        task_process_event_reminders, 
        task_background_ai_sync,
        task_renew_webhooks
    ]
    
    # Run reminder check every minute, and webhook renewal twice daily
    cron_jobs = [
        {'function': task_process_event_reminders, 'minute': '*', 'run_at_startup': True},
        {'function': task_renew_webhooks, 'hour': {0, 12}, 'minute': 0}
    ]
    
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    job_timeout = 300 
