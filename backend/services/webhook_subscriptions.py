import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import WebhookLogTable, WebhookSubscriptionTable
from backend.services.task_queue import enqueue_webhook_job

logger = logging.getLogger(__name__)
ALLOWED_WEBHOOK_EVENTS = ["booking.created", "booking.cancelled", "booking.rescheduled", "event_type.created", "event_type.updated", "event_type.deleted", "user.created", "user.updated"]

def _validate_events(events: list[str]) -> list[str]:
    if not isinstance(events, list) or not events:
        msg = "Webhook subscription must include at least one event."
        raise ValueError(msg)
    normalized: list[str] = []
    for event in events:
        if not isinstance(event, str) or event.strip() == "":
            continue
        event_value = event.strip()
        if event_value not in ALLOWED_WEBHOOK_EVENTS:
            msg = f"Unsupported webhook event: {event_value}"
            raise ValueError(msg)
        normalized.append(event_value)
    if not normalized:
        msg = "Webhook subscription must include at least one supported event."
        raise ValueError(msg)
    return normalized

async def list_webhook_subscriptions(db: AsyncSession, user_id: str) -> list[WebhookSubscriptionTable]:
    stmt = select(WebhookSubscriptionTable).where(and_(WebhookSubscriptionTable.user_id == user_id, not WebhookSubscriptionTable.is_deleted))
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_webhook_subscription(db: AsyncSession, user_id: str, webhook_id: str) -> WebhookSubscriptionTable | None:
    stmt = select(WebhookSubscriptionTable).where(and_(WebhookSubscriptionTable.id == webhook_id, WebhookSubscriptionTable.user_id == user_id, not WebhookSubscriptionTable.is_deleted))
    result = await db.execute(stmt)
    return result.scalars().first()

async def create_webhook_subscription(db: AsyncSession, user_id: str, url: str, events: list[str], secret: str, active: bool=True) -> WebhookSubscriptionTable:
    if not url or not isinstance(url, str):
        msg = "Webhook URL must be a non-empty string."
        raise ValueError(msg)
    if not secret or not isinstance(secret, str):
        msg = "Webhook secret must be a non-empty string."
        raise ValueError(msg)
    normalized_events = _validate_events(events)
    webhook = WebhookSubscriptionTable(user_id=user_id, url=url.strip(), events=normalized_events, active=active, secret=secret.strip())
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    return webhook

async def update_webhook_subscription(db: AsyncSession, user_id: str, webhook_id: str, url: str | None=None, events: list[str] | None=None, secret: str | None=None, active: bool | None=None) -> WebhookSubscriptionTable | None:
    webhook = await get_webhook_subscription(db, user_id, webhook_id)
    if not webhook:
        return None
    if url is not None:
        if not url.strip():
            msg = "Webhook URL must be a non-empty string."
            raise ValueError(msg)
        webhook.url = url.strip()
    if secret is not None:
        if not secret.strip():
            msg = "Webhook secret must be a non-empty string."
            raise ValueError(msg)
        webhook.secret = secret.strip()
    if events is not None:
        webhook.events = _validate_events(events)
    if active is not None:
        webhook.active = active
    await db.commit()
    await db.refresh(webhook)
    return webhook

async def delete_webhook_subscription(db: AsyncSession, user_id: str, webhook_id: str) -> bool:
    webhook = await get_webhook_subscription(db, user_id, webhook_id)
    if not webhook:
        return False
    if hasattr(webhook, "soft_delete"):
        await webhook.soft_delete(db, deleted_by=user_id)
    else:
        await db.delete(webhook)
        await db.commit()
    return True

async def list_webhook_logs(db: AsyncSession, user_id: str, webhook_id: str) -> list[WebhookLogTable]:
    webhook = await get_webhook_subscription(db, user_id, webhook_id)
    if not webhook:
        return []
    stmt = select(WebhookLogTable).where(WebhookLogTable.webhook_id == webhook.id).order_by(WebhookLogTable.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

async def create_webhook_log(db: AsyncSession, webhook_id: str, event: str, payload: Mapping[str, Any], attempts: int=1, next_retry_at: datetime | None=None) -> WebhookLogTable:
    if event not in ALLOWED_WEBHOOK_EVENTS:
        msg = f"Unsupported webhook event: {event}"
        raise ValueError(msg)
    log = WebhookLogTable(webhook_id=webhook_id, event=event, payload=payload, request_status=0, request_error=None, attempts=attempts, next_retry_at=next_retry_at)
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log

async def enqueue_webhook_notifications_for_event(db: AsyncSession, user_id: str, event: str, payload: Mapping[str, Any]) -> int:
    if event not in ALLOWED_WEBHOOK_EVENTS:
        msg = f"Unsupported webhook event: {event}"
        raise ValueError(msg)
    stmt = select(WebhookSubscriptionTable).where(and_(WebhookSubscriptionTable.user_id == user_id, WebhookSubscriptionTable.active))
    result = await db.execute(stmt)
    subscriptions = result.scalars().all()
    queued = 0
    for subscription in subscriptions:
        if event not in (subscription.events or []):
            continue
        webhook_body = {"event": event, "createdAt": datetime.now(UTC).isoformat(), "data": payload}
        try:
            log = await create_webhook_log(db, subscription.id, event, webhook_body)
        except Exception as exc:
            logger.error("Failed to create webhook log for subscription=%s event=%s: %s", subscription.id, event, exc, exc_info=True)
            continue
        try:
            await enqueue_webhook_job(url=subscription.url, payload=payload, webhook_id=subscription.id, log_id=log.id, secret=subscription.secret)
            queued += 1
        except Exception as exc:
            logger.error("Failed to enqueue webhook job for subscription=%s event=%s: %s", subscription.id, event, exc, exc_info=True)
            try:
                async with db.begin():
                    log.request_error = str(exc)
                    log.attempts = max(log.attempts or 1, 1)
            except Exception:
                logger.warning("Unable to update webhook log after enqueue failure for subscription=%s", subscription.id)
            continue
    return queued
