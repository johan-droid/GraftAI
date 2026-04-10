import logging
from datetime import datetime, timedelta, timezone
import pytz
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from backend.utils.db import AsyncSessionLocal
from backend.utils.webhook_signing import generate_webhook_signature
from backend.models.tables import UserTable, EventTable, BookingTable, WebhookLogTable
from backend.services.scheduler import push_event_to_external_calendar, update_event, delete_event
from backend.services.sync_engine import sync_user_calendar
from backend.services.calendar_sync import sync_calendar_for_user
from backend.services.notifications import (
    notify_event_created,
    notify_event_updated,
    notify_event_deleted,
    send_booking_reminder_to_organizer,
    send_custom_notification,
)
from backend.services.mail_service import send_email
from backend.services.queue_monitoring import start_queue_monitoring
from backend.utils.http_client import get_client

logger = logging.getLogger(__name__)

REGISTERED_TASKS = []

def task(func):
    """Decorator to register a function as a worker task."""
    REGISTERED_TASKS.append(func)
    return func

@task
async def task_sync_all_users(ctx):
    """Simple loop through users to trigger sync."""
    async with AsyncSessionLocal() as db:
        # STRIPPED: Simplified user fetch without status filters
        stmt = select(UserTable)
        users = (await db.execute(stmt)).scalars().all()
        
        for user in users:
            try:
                # Note: sync_user_calendar handles its own session/commits if needed
                # but here we pass the current session.
                await sync_user_calendar(db, str(user.id))
            except Exception as e:
                logger.error(f"Sync failed for {user.email}: {e}")

@task
async def task_sync_calendar(ctx, user_id: str):
    async with AsyncSessionLocal() as db:
        try:
            await sync_user_calendar(db, user_id)
            await sync_calendar_for_user(db, user_id)
        except Exception as e:
            logger.error(f"Calendar sync failed for user {user_id}: {e}")


@task
async def task_process_reminders(ctx):
    """Check for events starting in the next 60 minutes and send emails."""
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        lookahead = now + timedelta(minutes=60)
        
        stmt = select(EventTable).where(
            and_(
                EventTable.start_time >= now,
                EventTable.start_time <= lookahead,
                EventTable.is_reminded == False
            )
        )
        events = (await db.execute(stmt)).scalars().all()
        
        for event in events:
            user = await db.get(UserTable, event.user_id)
            if user:
                try:
                    await send_email(
                        user.email,
                        f"Reminder: {event.title}",
                        f"Hi {user.full_name or 'there'}, your meeting '{event.title}' starts soon at {event.start_time}."
                    )
                    event.is_reminded = True
                except Exception as e:
                    logger.error(f"Failed to send reminder for event {event.id}: {e}")
        
        await db.commit()


@task
async def task_send_booking_reminders(ctx):
    """Send organizer reminders for bookings that start ~24 hours from now."""
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        reminder_target = now + timedelta(hours=24)
        window_start = reminder_target - timedelta(minutes=30)
        window_end = reminder_target + timedelta(minutes=30)

        stmt = (
            select(BookingTable)
            .options(
                selectinload(BookingTable.user),
                selectinload(BookingTable.event),
                selectinload(BookingTable.event_type),
            )
            .where(
                and_(
                    BookingTable.status.in_(["confirmed", "rescheduled", "accepted"]),
                    BookingTable.start_time >= window_start,
                    BookingTable.start_time <= window_end,
                    BookingTable.is_reminder_sent == False,
                )
            )
        )

        bookings = (await db.execute(stmt)).scalars().all()
        if not bookings:
            return

        sent = 0
        for booking in bookings:
            organizer = booking.user
            if not organizer:
                continue

            tz_name = organizer.timezone or "UTC"
            try:
                organizer_tz = pytz.timezone(tz_name)
            except Exception:
                organizer_tz = pytz.UTC
                tz_name = "UTC"

            event_title = "Booked Meeting"
            if booking.event and booking.event.title:
                event_title = booking.event.title
            elif booking.event_type and booking.event_type.name:
                event_title = booking.event_type.name

            organizer_start_time = booking.start_time.astimezone(organizer_tz).strftime("%Y-%m-%d %I:%M %p")
            organizer_end_time = booking.end_time.astimezone(organizer_tz).strftime("%Y-%m-%d %I:%M %p")

            try:
                await send_booking_reminder_to_organizer(
                    organizer_email=organizer.email,
                    organizer_name=organizer.full_name or organizer.username or organizer.email,
                    attendee_name=booking.full_name,
                    attendee_email=booking.email,
                    event_title=event_title,
                    organizer_start_time=organizer_start_time,
                    organizer_end_time=organizer_end_time,
                    organizer_timezone=tz_name,
                    booking_id=booking.id,
                )
                booking.is_reminder_sent = True
                sent += 1
            except Exception as e:
                logger.error(f"Failed to send booking reminder for booking {booking.id}: {e}")

        if sent:
            await db.commit()
            logger.info("Booking reminders sent: %s", sent)

@task
async def task_send_email(ctx, booking_id: str, email_type: str, extra: dict = None):
    async with AsyncSessionLocal() as db:
        stmt = select(BookingTable).options(selectinload(BookingTable.event)).where(BookingTable.id == booking_id)
        booking = (await db.execute(stmt)).scalars().first()
        if not booking:
            logger.warning(f"Email job failed: booking {booking_id} not found")
            return

        event = booking.event
        if not event:
            logger.warning(f"Email job failed: event for booking {booking_id} not found")
            return

        payload = {
            "id": event.id,
            "title": event.title,
            "start_time": event.start_time.strftime("%A, %B %d at %I:%M %p"),
            "end_time": event.end_time.strftime("%A, %B %d at %I:%M %p"),
            "meeting_link": event.meeting_url,
            "is_meeting": event.is_meeting,
            **(extra or {}),
        }

        try:
            if email_type == "confirmation":
                await notify_event_created([booking.email], [], payload)
            elif email_type == "new_booking":
                organizer_email = payload.get("organizer_email")
                if organizer_email:
                    await send_custom_notification(
                        organizer_email,
                        f"New booking for {event.title}",
                        f"A new booking has been scheduled for {event.title} on {payload['start_time']}.",
                        html_body=f"<p>A new booking has been scheduled for <strong>{event.title}</strong> on {payload['start_time']}.</p>",
                    )
                else:
                    logger.warning(f"Missing organizer_email for new_booking job {booking_id}")
            elif email_type == "reminder":
                await notify_event_updated([booking.email], [], payload)
            elif email_type == "cancellation":
                await notify_event_deleted([booking.email], [], payload)
            else:
                logger.warning(f"Unknown email_type '{email_type}' for booking {booking_id}")
        except Exception as e:
            logger.error(f"Failed to send {email_type} email for booking {booking_id}: {e}")

@task
async def task_send_booking_confirmation(ctx, booking_id: str):
    async with AsyncSessionLocal() as db:
        stmt = select(BookingTable).options(selectinload(BookingTable.event)).where(BookingTable.id == booking_id)
        booking = (await db.execute(stmt)).scalars().first()
        if not booking:
            logger.warning(f"Booking confirmation failed: booking {booking_id} not found")
            return

        event = booking.event
        if not event:
            logger.warning(f"Booking confirmation failed: event for booking {booking_id} not found")
            return

        notification_data = {
            "id": event.id,
            "title": event.title,
            "start_time": event.start_time.strftime("%A, %B %d at %I:%M %p"),
            "end_time": event.end_time.strftime("%A, %B %d at %I:%M %p"),
            "meeting_link": event.meeting_url,
            "is_meeting": event.is_meeting,
        }

        try:
            await notify_event_created([booking.email], [], notification_data)
        except Exception as e:
            logger.error(f"Failed to send booking confirmation for {booking_id}: {e}")

@task
async def task_send_webhook(
    ctx,
    url: str,
    event: str,
    data: dict,
    attempt: int = 1,
    webhook_id: str | None = None,
    log_id: str | None = None,
    secret: str | None = None,
):
    created_at = datetime.now(timezone.utc)
    payload = {
        "event": event,
        "createdAt": created_at.isoformat(),
        "data": data,
    }
    headers = {"Content-Type": "application/json"}
    if secret:
        signature = generate_webhook_signature(secret, payload)
        headers["X-Cal-Signature"] = signature
        headers["X-Cal-Timestamp"] = str(int(created_at.timestamp() * 1000))

    attempt = getattr(ctx, "job_try", None) if hasattr(ctx, "job_try") else ctx.get("job_try", 1)
    if attempt is None:
        attempt = 1

    try:
        client = await get_client()
        response = await client.post(url, json=payload, headers=headers, timeout=10.0)
        status = response.status_code

        if log_id:
            async with AsyncSessionLocal() as db:
                log = await db.get(WebhookLogTable, log_id)
                if log:
                    log.request_status = status
                    log.request_error = None
                    log.attempts = max(log.attempts or 1, attempt)
                    log.next_retry_at = None
                    await db.commit()

        if status >= 400:
            raise RuntimeError(f"Webhook failed with status {status}")
        logger.info(
            "Webhook delivered successfully to %s (status=%s, webhook_id=%s, attempt=%s)",
            url,
            status,
            webhook_id,
            attempt,
        )
    except Exception as e:
        if log_id:
            async with AsyncSessionLocal() as db:
                log = await db.get(WebhookLogTable, log_id)
                if log:
                    log.request_status = 0
                    log.request_error = str(e)
                    log.attempts = max(log.attempts or 1, attempt)
                    log.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=5)
                    await db.commit()

        logger.error(
            "Webhook delivery failed (webhook_id=%s, attempt=%s) to %s: %s",
            webhook_id,
            attempt,
            url,
            e,
            exc_info=True,
        )
        if attempt < 5:
            raise
        logger.error(
            "Webhook permanently failed after %s attempts for webhook_id=%s url=%s",
            attempt,
            webhook_id,
            url,
        )

@task
async def task_track_analytics(ctx, event: str, properties: dict):
    logger.info(f"Analytics event queued: {event} properties={properties}")

@task
async def task_create_calendar_event(ctx, event_id: str):
    async with AsyncSessionLocal() as db:
        event = await db.get(EventTable, event_id)
        if not event:
            logger.warning(f"Calendar create failed: event {event_id} not found")
            return

        if not event.meeting_provider:
            logger.info(f"Calendar create skipped: event {event_id} has no meeting provider")
            return

        if event.external_id:
            logger.info(f"Calendar create skipped: event {event_id} already has external_id")
            return

        try:
            await push_event_to_external_calendar(db, event_id)
        except Exception as e:
            logger.error(f"Failed to push event {event_id} to external calendar: {e}")

@task
async def task_update_calendar_event(ctx, event_id: str, update_data: dict = None):
    async with AsyncSessionLocal() as db:
        event = await db.get(EventTable, event_id)
        if not event:
            logger.warning(f"Calendar update failed: event {event_id} not found")
            return

        try:
            await update_event(db, event_id, event.user_id, update_data or {})
        except Exception as e:
            logger.error(f"Failed to update calendar event {event_id}: {e}")

@task
async def task_delete_calendar_event(ctx, event_id: str):
    async with AsyncSessionLocal() as db:
        event = await db.get(EventTable, event_id)
        if not event:
            logger.warning(f"Calendar delete failed: event {event_id} not found")
            return

        try:
            await delete_event(db, event_id, event.user_id)
        except Exception as e:
            logger.error(f"Failed to delete calendar event {event_id}: {e}")

@task
async def task_send_sms(ctx, phone_number: str, message: str):
    """Send SMS notification - requires Twilio/SNS configuration."""
    import os
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    if not twilio_sid:
        logger.warning("SMS not configured - set TWILIO_ACCOUNT_SID to enable")
        return
    # TODO: Implement Twilio integration
    logger.info(f"SMS queued: {phone_number}")

@task
async def task_update_crm(ctx, booking_id: str):
    """Update external CRM - requires CRM integration setup."""
    import os
    crm_api_key = os.getenv("CRM_API_KEY")
    if not crm_api_key:
        logger.debug(f"CRM update skipped for booking {booking_id} - no CRM configured")
        return
    # TODO: Implement CRM integration (Salesforce, HubSpot, etc.)
    logger.info(f"CRM update queued for booking {booking_id}")

@task
async def task_daily_cleanup(ctx):
    """Purge old logs or expired data."""
    logger.info("Running daily cleanup...")

# ── Arq Worker Settings ───────────────────────────────────────────────────────

async def _worker_startup(ctx):
    logger.info("Worker started.")
    start_queue_monitoring()


class WorkerSettings:
    """Standard Arq configuration."""
    functions = REGISTERED_TASKS
    on_startup = _worker_startup
    cron_jobs = [
        {"coroutine": task_sync_all_users, "minute": {0, 30}},
        {"coroutine": task_process_reminders, "minute": "*"},
        {"coroutine": task_send_booking_reminders, "minute": 5},
        {"coroutine": task_daily_cleanup, "hour": 3, "minute": 0},
    ]
