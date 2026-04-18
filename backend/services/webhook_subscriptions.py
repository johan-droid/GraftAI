import logging
from datetime import datetime, timezone
from typing import Any, List, Mapping, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import WebhookSubscriptionTable, WebhookLogTable
from backend.utils.arq_utils import enqueue_job

logger = logging.getLogger(__name__)

ALLOWED_WEBHOOK_EVENTS = [
    "booking.created",
    "booking.cancelled",
    "booking.rescheduled",
    "event_type.created",
    "event_type.updated",
    "event_type.deleted",
    "user.created",
    "user.updated",
]


def _validate_events(events: List[str]) -> List[str]:
    if not isinstance(events, list) or not events:
        raise ValueError("Webhook subscription must include at least one event.")

    normalized: List[str] = []
    for event in events:
        if not isinstance(event, str) or event.strip() == "":
            continue
        event_value = event.strip()
        if event_value not in ALLOWED_WEBHOOK_EVENTS:
            raise ValueError(f"Unsupported webhook event: {event_value}")
        normalized.append(event_value)

    if not normalized:
        raise ValueError(
            "Webhook subscription must include at least one supported event."
        )
    return normalized


async def list_webhook_subscriptions(
    db: AsyncSession, user_id: str
) -> List[WebhookSubscriptionTable]:
    stmt = select(WebhookSubscriptionTable).where(
        WebhookSubscriptionTable.user_id == user_id
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_webhook_subscription(
    db: AsyncSession, user_id: str, webhook_id: str
) -> Optional[WebhookSubscriptionTable]:
    stmt = select(WebhookSubscriptionTable).where(
        and_(
            WebhookSubscriptionTable.id == webhook_id,
            WebhookSubscriptionTable.user_id == user_id,
        )
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_webhook_subscription(
    db: AsyncSession,
    user_id: str,
    url: str,
    events: List[str],
    secret: str,
    active: bool = True,
) -> WebhookSubscriptionTable:
    if not url or not isinstance(url, str):
        raise ValueError("Webhook URL must be a non-empty string.")
    if not secret or not isinstance(secret, str):
        raise ValueError("Webhook secret must be a non-empty string.")

    normalized_events = _validate_events(events)
    webhook = WebhookSubscriptionTable(
        user_id=user_id,
        url=url.strip(),
        events=normalized_events,
        active=active,
        secret=secret.strip(),
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    return webhook


async def update_webhook_subscription(
    db: AsyncSession,
    user_id: str,
    webhook_id: str,
    url: Optional[str] = None,
    events: Optional[List[str]] = None,
    secret: Optional[str] = None,
    active: Optional[bool] = None,
) -> Optional[WebhookSubscriptionTable]:
    webhook = await get_webhook_subscription(db, user_id, webhook_id)
    if not webhook:
        return None

    if url is not None:
        if not url.strip():
            raise ValueError("Webhook URL must be a non-empty string.")
        webhook.url = url.strip()

    if secret is not None:
        if not secret.strip():
            raise ValueError("Webhook secret must be a non-empty string.")
        webhook.secret = secret.strip()

    if events is not None:
        webhook.events = _validate_events(events)

    if active is not None:
        webhook.active = active

    await db.commit()
    await db.refresh(webhook)
    return webhook


async def delete_webhook_subscription(
    db: AsyncSession, user_id: str, webhook_id: str
) -> bool:
    webhook = await get_webhook_subscription(db, user_id, webhook_id)
    if not webhook:
        return False
    await db.delete(webhook)
    await db.commit()
    return True


async def list_webhook_logs(
    db: AsyncSession, user_id: str, webhook_id: str
) -> List[WebhookLogTable]:
    webhook = await get_webhook_subscription(db, user_id, webhook_id)
    if not webhook:
        return []

    stmt = (
        select(WebhookLogTable)
        .where(WebhookLogTable.webhook_id == webhook.id)
        .order_by(WebhookLogTable.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def create_webhook_log(
    db: AsyncSession,
    webhook_id: str,
    event: str,
    payload: Mapping[str, Any],
    attempts: int = 1,
    next_retry_at: Optional[datetime] = None,
) -> WebhookLogTable:
    if event not in ALLOWED_WEBHOOK_EVENTS:
        raise ValueError(f"Unsupported webhook event: {event}")

    log = WebhookLogTable(
        webhook_id=webhook_id,
        event=event,
        payload=payload,
        request_status=0,
        request_error=None,
        attempts=attempts,
        next_retry_at=next_retry_at,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def enqueue_webhook_notifications_for_event(
    db: AsyncSession,
    user_id: str,
    event: str,
    payload: Mapping[str, Any],
) -> int:
    if event not in ALLOWED_WEBHOOK_EVENTS:
        raise ValueError(f"Unsupported webhook event: {event}")

    stmt = select(WebhookSubscriptionTable).where(
        and_(
            WebhookSubscriptionTable.user_id == user_id,
            WebhookSubscriptionTable.active == True,
        )
    )
    result = await db.execute(stmt)
    subscriptions = result.scalars().all()

    queued = 0
    for subscription in subscriptions:
        if event not in (subscription.events or []):
            continue

        webhook_body = {
            "event": event,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        }

        try:
            log = await create_webhook_log(db, subscription.id, event, webhook_body)
        except Exception as exc:
            logger.error(
                "Failed to create webhook log for subscription=%s event=%s: %s",
                subscription.id,
                event,
                exc,
                exc_info=True,
            )
            continue

        try:
            await enqueue_job(
                "task_send_webhook",
                url=subscription.url,
                event=event,
                data=payload,
                webhook_id=subscription.id,
                log_id=log.id,
                secret=subscription.secret,
            )
            queued += 1
        except Exception as exc:
            logger.error(
                "Failed to enqueue webhook job for subscription=%s event=%s: %s",
                subscription.id,
                event,
                exc,
                exc_info=True,
            )
            try:
                async with db.begin():
                    log.request_error = str(exc)
                    log.attempts = max(log.attempts or 1, 1)
            except Exception:
                logger.warning(
                    "Unable to update webhook log after enqueue failure for subscription=%s",
                    subscription.id,
                )
            continue

    return queued
