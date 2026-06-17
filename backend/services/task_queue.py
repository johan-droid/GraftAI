"""
Unified task enqueue module.

Replaces arq_utils.py and jobs.py. All background job enqueue calls
route through Celery's apply_async() for durable, distributed execution.
"""
import logging
from collections.abc import Mapping
from typing import Any

from backend.tasks.automation_tasks import (
    provision_jitsi_meeting as celery_provision_jitsi_meeting,
    provision_shortlink as celery_provision_shortlink,
)
from backend.tasks.calendar_tasks import (
    create_calendar_event as celery_create_calendar_event,
    sync_user_calendar as celery_sync_user_calendar,
)
from backend.tasks.email_tasks import send_booking_confirmation
from backend.tasks.webhook_tasks import deliver_webhook

logger = logging.getLogger(__name__)


async def enqueue_email_job(booking_id: str, email_type: str, extra: Mapping[str, Any] | None = None):
    send_booking_confirmation.apply_async(
        kwargs={
            "booking_id": booking_id,
            "attendee_email": (extra or {}).get("email", ""),
            "attendee_name": (extra or {}).get("name", ""),
            "meeting_title": (extra or {}).get("title", ""),
            "start_time": (extra or {}).get("start_time", ""),
            "end_time": (extra or {}).get("end_time", ""),
            "meeting_url": (extra or {}).get("meeting_url"),
        }
    )


async def enqueue_calendar_job(booking_id: str, action: str, extra: Mapping[str, Any] | None = None):
    celery_create_calendar_event.apply_async(
        kwargs={
            "user_id": (extra or {}).get("user_id", ""),
            "booking_id": booking_id,
            "provider": (extra or {}).get("provider", "google"),
            "event_data": dict(extra) if extra else None,
        }
    )


async def enqueue_webhook_job(
    url: str, payload: Mapping[str, Any], attempt: int = 1, webhook_id: str | None = None, log_id: str | None = None, secret: str | None = None
):
    deliver_webhook.apply_async(
        kwargs={
            "webhook_id": webhook_id or "",
            "subscriber_url": url,
            "payload": dict(payload),
            "secret": secret,
        }
    )


async def enqueue_analytics_job(event: str, properties: Mapping[str, Any]):
    logger.info("Analytics event queued: %s properties=%s", event, properties)


async def enqueue_provision_shortlink(booking_id: str):
    celery_provision_shortlink.apply_async(kwargs={"booking_id": booking_id})


async def enqueue_provision_jitsi_meeting(booking_id: str):
    celery_provision_jitsi_meeting.apply_async(kwargs={"booking_id": booking_id})


async def enqueue_calendar_sync(user_id: str):
    celery_sync_user_calendar.apply_async(kwargs={"user_id": user_id})


async def enqueue_welcome_email(user_email: str, full_name: str):
    logger.info("Welcome email queued for %s", user_email)
