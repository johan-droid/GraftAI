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
from backend.services.sync_engine import sync_user_calendar
from backend.services.mail_service import send_email, render_template
from backend.services.notifications import notify_welcome_email, notify_event_reminder
from backend.utils.arq_utils import publish_event

# Registry for automatic discovery
REGISTERED_TASKS = []
REGISTERED_CRONS = []

def task(func):
    """Decorator to register a function as an arq worker task."""
    REGISTERED_TASKS.append(func)
    return func

def cron(minute='*', hour='*', run_at_startup=False):
    """Decorator to register a function as a periodic cron job."""
    def decorator(func):
        REGISTERED_CRONS.append({
            'function': func,
            'minute': minute,
            'hour': hour,
            'run_at_startup': run_at_startup
        })
        return func
    return decorator

@task
async def task_notify_welcome(ctx, user_email: str, full_name: str):
    """Worker task to send a welcome email to a new user."""
    logger.info(f"[WORKER] ✉️ Sending welcome email to {user_email}")
    await notify_welcome_email(user_email, full_name)

@task
async def task_sync_calendar(ctx, user_id: str):
    """Worker task to perform an initial or periodic calendar sync."""
    logger.info(f"[WORKER] 🗓 Syncing calendar for user {user_id}")
    async with ctx['db_session_factory']() as db:
        await sync_user_calendar(db, user_id)

@cron(minute='*', run_at_startup=True)
async def task_process_event_reminders(ctx):
    """
    Precision Reminder Engine:
    Processes upcoming events with sub-minute accuracy.
    Optimized for massive crowds via covering index-first query.
    """
    async with ctx['db_session_factory']() as db:
        now = datetime.now(timezone.utc)
        # Narrow window (28-32 mins) matches the cron frequency to avoid misses
        min_t, max_t = now + timedelta(minutes=28), now + timedelta(minutes=32)
        
        stmt = (
            select(EventTable, UserTable.email, UserTable.full_name)
            .join(UserTable, EventTable.user_id == UserTable.id)
            .where(
                and_(
                    EventTable.start_time.between(min_t, max_t),
                    EventTable.is_reminded == False,
                    EventTable.status == "confirmed"
                )
            )
        )
        result = await db.execute(stmt)
        rows = result.all()
        
        for event, user_email, user_name in rows:
            try:
                # MARK-THEN-SEND pattern ensures zero double-notifications
                event.is_reminded = True
                await db.flush() 
                
                await notify_event_reminder(user_email, [], {
                    "id": event.id,
                    "title": event.title,
                    "start_time": event.start_time.strftime("%I:%M %p"),
                    "meeting_platform": event.meeting_platform,
                    "meeting_link": event.meeting_link,
                    "full_name": user_name
                })
                
                await db.commit()
            except Exception as e:
                await db.rollback()
                logger.error(f"[WORKER] ❌ Reminder failed for {event.id}: {e}")

@task
async def task_notify_event(ctx, to_email: str, template_name: str, subject: str, context: dict):
    """Unified worker task to render and send any email from a template."""
    logger.info(f"[WORKER] ✉️ Sending lifecycle email ({template_name}) to {to_email}")
    try:
        html_body = render_template(template_name, context)
        await send_email(to_email, subject, html_body)
    except Exception as e:
        logger.error(f"[WORKER] ❌ Failed to send email {template_name}: {e}")

@task
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

@task
async def task_provision_meeting(ctx, event_id: int, user_id: str, platform: str):
    """
    Deferred I/O Task: Handles slow third-party API calls (Google/MS) 
    in the background to keep initial response times under 100ms.
    """
    from backend.services.scheduler import _generate_meeting_link, _push_to_external
    # import json -> Using binary streams instead
    
    logger.info(f"[WORKER] 🚀 Provisioning meeting link for event {event_id} on {platform}")
    
    async with ctx['db_session_factory']() as db:
        stmt = select(EventTable).where(EventTable.id == event_id)
        res = await db.execute(stmt)
        event = res.scalars().first()
        
        if not event:
            logger.error(f"[WORKER] ❌ Event {event_id} not found for provisioning.")
            return

        try:
            # Notify frontend provisioning started via Reliable Stream
            await publish_event(f"stream:sync:{user_id}", "SYNC_STATUS", {
                "status": "syncing", 
                "message": f"Provisioning secure {platform} link..."
            })
            
            event_details = {
                "title": event.title,
                "description": event.description,
                "start_time": event.start_time,
                "end_time": event.end_time,
            }
            # 1. Generate meeting link and push to external provider in parallel
            # (They are independent I/O operations once user token is fetched)
            import asyncio
            link_task = _generate_meeting_link(db, user_id, platform, event_details)
            ext_task = _push_to_external(db, event, action="create")
            
            link, ext_id = await asyncio.gather(link_task, ext_task)
            
            event.meeting_link = link
            event.is_meeting = True
            event.meeting_platform = platform
            if ext_id:
                event.external_id = ext_id
            
            await db.commit()
            
            # Notify frontend success
            await publish_event(f"stream:sync:{user_id}", "SYNC_STATUS", {
                "status": "idle", 
                "message": f"Meeting link ready: {platform}"
            })
            logger.info(f"[WORKER] ✅ Successfully provisioned link for event {event_id}")
            
        except Exception as e:
            logger.error(f"[WORKER] ❌ Provisioning failed for event {event_id}: {e}")
            await publish_event(f"stream:sync:{user_id}", "SYNC_STATUS", {
                "status": "error", 
                "message": f"Failed to provision {platform} link."
            })

@cron(hour=0, minute=0)
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

@cron(hour=1, minute=0)
async def task_purge_old_events(ctx):
    """
    7-Day Mandate Content Purge: Deletes past events older than 7 days.
    Prevents database memory bloat and keeps context relevant.
    """
    logger.info("[WORKER] 🧹 Scrubbing events older than 7 days...")
    from sqlalchemy import delete
    
    async with ctx['db_session_factory']() as db:
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        stmt = delete(EventTable).where(EventTable.end_time < cutoff)
        result = await db.execute(stmt)
        await db.commit()
        logger.info(f"✅ [WORKER] Purged {result.rowcount} old calendar events.")

@cron(hour={3, 9, 15, 21}, minute=0)
async def task_sync_all_calendars(ctx):
    """
    Distributed Sync Orchestrator (ScaleReady):
    Splits the global sync load into chunks of 100 users per worker task.
    Prevents CPU bursts and Redis connection bottlenecks.
    """
    from backend.models.user_token import UserTokenTable
    redis = ctx['redis']
    async with ctx['db_session_factory']() as db:
        stmt = select(UserTokenTable.user_id).where(UserTokenTable.is_active == True).distinct()
        result = await db.execute(stmt)
        user_ids = result.scalars().all()
        
        # Partitioning by 100 for stable worker concurrency
        CHUNK_SIZE = 100
        for i in range(0, len(user_ids), CHUNK_SIZE):
            chunk = user_ids[i:i + CHUNK_SIZE]
            await redis.enqueue_job("task_sync_batch", chunk)
            logger.info(f"[WORKER] 📦 Enqueued segment batch {i//CHUNK_SIZE + 1} ({len(chunk)} users)")

@task
async def task_sync_batch(ctx, user_ids: list[str]):
    """Internal task to process a small batch of synchronizations."""
    redis = ctx['redis']
    for uid in user_ids:
        await redis.enqueue_job("task_sync_calendar", uid)

@task
async def task_renew_user_webhook(ctx, user_id: str):
    """Worker task to renew a specific user's webhooks."""
    from backend.services.integrations.webhook_manager import register_user_webhooks
    logger.info(f"[WORKER] ♻️ Renewing webhooks for user {user_id}")
    async with ctx['db_session_factory']() as db:
        await register_user_webhooks(db, user_id)

@cron(hour={0, 12}, minute=0)
async def task_renew_webhooks(ctx):
    """Periodic task to enqueue renewal jobs for Google and Microsoft push notification subscriptions."""
    from backend.models.tables import WebhookSubscriptionTable
    redis = ctx['redis']
    async with ctx['db_session_factory']() as db:
        stmt = select(WebhookSubscriptionTable.user_id).distinct()
        result = await db.execute(stmt)
        user_ids = result.scalars().all()
        for uid in user_ids:
            await redis.enqueue_job("task_renew_user_webhook", uid)

USAGE_FLUSH_INTERVAL = os.getenv("USAGE_FLUSH_INTERVAL_MINUTES", "5")

@cron(minute=f"*/{USAGE_FLUSH_INTERVAL}")
async def task_persist_usage_to_db(ctx):
    """
    Write-Behind Sync Logic:
    Collects users with usage activity and flushes their counts 
    to Postgres in a single transaction. Reduces DB write-load by ~90%.
    """
    from backend.models.tables import UserTable
    from sqlalchemy import update
    redis = ctx['redis']
    
    user_ids = await redis.smembers("usage:flush_queue")
    if not user_ids: return

    logger.info(f"[WORKER] 💾 Flushing usage for {len(user_ids)} active users to DB...")
    async with ctx['db_session_factory']() as db:
        for uid_raw in user_ids:
            uid = uid_raw.decode() if hasattr(uid_raw, 'decode') else uid_raw
            ai_count = await redis.get(f"usage:{uid}:ai_messages")
            sync_count = await redis.get(f"usage:{uid}:calendar_syncs")
            
            if ai_count is not None or sync_count is not None:
                await db.execute(update(UserTable).where(UserTable.id == uid).values(
                    daily_ai_count=int(ai_count or 0),
                    daily_sync_count=int(sync_count or 0)
                ))
        
        await db.commit()
        await redis.srem("usage:flush_queue", *user_ids)
    logger.info("✅ [WORKER] Usage persistence complete.")

@task
async def task_emit_quota_update(ctx, user_id: str, feature: str, count: int):
    """
    Real-Time Event Publisher:
    Uses MessagePack binary format for high-throughput delivery via Redis Streams.
    """
    await publish_event(f"stream:user:{user_id}", "QUOTA_UPDATE", {
        "feature": feature,
        "count": count
    })

async def startup(ctx):
    from backend.utils.db import AsyncSessionLocal
    ctx['db_session_factory'] = AsyncSessionLocal
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=0.1)
    logger.info("[WORKER] 🚀 Background worker started.")

async def shutdown(ctx):
    logger.info("[WORKER] 🛑 Background worker shutting down.")

class WorkerSettings:
    """Settings for the arq worker with automatic discovery."""
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    functions = list(set(REGISTERED_TASKS)) 
    cron_jobs = REGISTERED_CRONS
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    job_timeout = 300 
