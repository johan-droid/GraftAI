"""
Arq-backed background job helper.

This module centralizes the application's job enqueue API so callers can
enqueue email/calendar/webhook/analytics work consistently.
"""

from typing import Any, Mapping, Optional

from backend.utils.arq_utils import enqueue_job as _enqueue_job


async def enqueue_email_job(
    booking_id: str,
    email_type: str,
    extra: Optional[Mapping[str, Any]] = None,
):
    return await _enqueue_job(
        "task_send_email",
        booking_id=booking_id,
        email_type=email_type,
        extra=extra or {},
    )


async def enqueue_calendar_job(
    booking_id: str,
    action: str,
    extra: Optional[Mapping[str, Any]] = None,
):
    return await _enqueue_job(
        "task_create_calendar_event"
        if action == "create"
        else "task_update_calendar_event"
        if action == "update"
        else "task_delete_calendar_event",
        booking_id=booking_id,
        action=action,
        extra=extra or {},
    )


async def enqueue_webhook_job(url: str, payload: Mapping[str, Any], attempt: int = 1):
    return await _enqueue_job(
        "task_send_webhook",
        url=url,
        payload=payload,
        attempt=attempt,
    )


async def enqueue_analytics_job(event: str, properties: Mapping[str, Any]):
    return await _enqueue_job(
        "task_track_analytics",
        event=event,
        properties=properties,
    )
