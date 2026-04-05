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
from backend.services.email import send_email, render_template

async def task_notify_welcome(ctx, user_email: str, full_name: str):
    """Worker task to send a welcome email to a new user."""
    logger.info(f"[WORKER] ✉️ Sending welcome email to {user_email}")
    await notify_welcome_email(user_email, full_name)

async def task_sync_calendar(ctx, user_id: str):
    """Worker task to perform an initial or periodic calendar sync."""
    logger.info(f"[WORKER] 🗓 Syncing calendar for user {user_id}")
    async with ctx['db_session_factory']() as db:
        await sync_user_calendar(db, user_id)

async def task_process_event_reminders(ctx):
    """
    Periodic task to check for upcoming events and send reminders.
    Matches events starting exactly ~30 minutes (28-32 min window) from now.
    """
    logger.info("[WORKER] 🔔 Scanning for events starting in exactly 30 minutes...")
    async with ctx['db_session_factory']() as db:
        now = datetime.now(timezone.utc)
        min_threshold = now + timedelta(minutes=28)
        max_threshold = now + timedelta(minutes=32)
        
        stmt = (
            select(EventTable, UserTable.email, UserTable.full_name)
            .join(UserTable, EventTable.user_id == UserTable.id)
            .where(
                and_(
                    EventTable.start_time >= min_threshold,
                    EventTable.start_time <= max_threshold,
                    EventTable.is_reminded == False,
                    EventTable.status == "confirmed"
                )
            )
        )
        result = await db.execute(stmt)
        rows = result.all()
        
        for event, user_email, user_name in rows:
            try:
                # Logic Hole Audit: Mark as processing BEFORE sending to avoid duplicates if crash occurs mid-loop
                event.is_reminded = True
                await db.flush() # Ensure change is tracked
                
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
                
                # Send the reminder
                await notify_event_reminder(user_email, [], event_data)
                
                # Commit immediately for this specific event to prevent re-processing
                await db.commit()
                logger.info(f"[WORKER] 🔔 Reminder sent and committed for event '{event.title}' to {user_email}")
            except Exception as e:
                # Rollback if send fails so we can retry in the next window (if within 28-32 mins)
                await db.rollback()
                logger.error(f"[WORKER] ❌ Failed to send reminder for event {event.id}: {e}")

async def task_notify_event(ctx, to_email: str, template_name: str, subject: str, context: dict):
    """Unified worker task to render and send any email from a template."""
    logger.info(f"[WORKER] ✉️ Sending lifecycle email ({template_name}) to {to_email}")
    try:
        html_body = render_template(template_name, context)
        await send_email(to_email, subject, html_body)
    except Exception as e:
        logger.error(f"[WORKER] ❌ Failed to send email {template_name}: {e}")

async def task_background_ai_sync(ctx, event_id: int, user_id: str, action: str = "upsert"):
    """Worker task to perform Pinecone operations in the background."""
    from backend.services.ai_sync import sync_event_to_vector_store, purge_event_from_vector_store
    if action == "delete":
        await purge_event_from_vector_store(event_id, user_id)
        return
    async with ctx['db_session_factory']() as db:
        stmt = select(EventTable).where(EventTable.id == event_id)
        result = await db.execute(stmt)
        event = result.scalars().first()
        if event:
            await sync_event_to_vector_store(event)

async def task_purge_expired_accounts(ctx):
    """
    Daily Retention Worker: Permanently purges accounts soft-deleted >30 days ago.
    This fulfills both GDPR right-to-erasure and business retention policies.
    """
    logger.info("[WORKER] 🧹 Starting Daily Retention Audit...")
    from backend.models.tables import UserTable
    from sqlalchemy import delete
    
    async with ctx['db_session_factory']() as db:
        retention_threshold = datetime.now(timezone.utc) - timedelta(days=30)
        
        # Find and Delete (Cascades will handle child records: events, sessions, etc.)
        stmt = delete(UserTable).where(
            and_(
                UserTable.deleted_at is not None,
                UserTable.deleted_at < retention_threshold
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        
        # rowcount represents how many users were purged
        count = result.rowcount
        if count > 0:
            logger.info(f"✅ [WORKER] Successfully purged {count} expired accounts (GDPR Cycle).")
        else:
            logger.info("✅ [WORKER] Retention audit complete. No accounts eligible for purge.")

async def task_renew_webhooks(ctx):
    """Periodic task to renew Google and Microsoft push notification subscriptions."""
    from backend.services.integrations.webhook_manager import renew_all_expiring_subscriptions
    async with ctx['db_session_factory']() as db:
        await renew_all_expiring_subscriptions(db)

async def startup(ctx):
    from backend.utils.db import get_async_session_factory
    ctx['db_session_factory'] = get_async_session_factory()
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=0.1, environment=os.getenv("ENV", "production"))
    logger.info("[WORKER] 🚀 Background worker started.")

async def shutdown(ctx):
    logger.info("[WORKER] 🛑 Background worker shutting down.")

class WorkerSettings:
    """Settings for the arq worker."""
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    functions = [
        task_notify_welcome, 
        task_sync_calendar, 
        task_process_event_reminders, 
        task_background_ai_sync,
        task_renew_webhooks,
        task_notify_event,
        task_purge_expired_accounts
    ]
    cron_jobs = [
        {'function': task_process_event_reminders, 'minute': '*', 'run_at_startup': True},
        {'function': task_renew_webhooks, 'hour': {0, 12}, 'minute': 0},
        {'function': task_purge_expired_accounts, 'hour': 0, 'minute': 0} # Daily Midnight Purge
    ]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    job_timeout = 300 
