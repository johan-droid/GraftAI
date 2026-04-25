import hmac
import hashlib
import json
import logging
import os
from datetime import datetime
from typing import List, Optional

import stripe

from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from pydantic import BaseModel, AnyHttpUrl, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.api.deps import get_db, get_current_user
from backend.models.tables import WebhookSubscriptionTable, UserTable
from backend.services.calendar_sync import invalidate_user_calendar_busy_cache
from backend.services.webhook_subscriptions import (
    list_webhook_subscriptions,
    create_webhook_subscription,
    update_webhook_subscription,
    delete_webhook_subscription,
    list_webhook_logs,
)
from backend.utils.cache import (
    invalidate_user_calendar_cache,
    invalidate_user_cache_pattern,
    acquire_lock,
)
from backend.utils.arq_utils import enqueue_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookSubscriptionPayload(BaseModel):
    url: AnyHttpUrl
    events: List[str] = Field(..., min_length=1)
    secret: str = Field(..., min_length=8)
    active: Optional[bool] = True


class WebhookSubscriptionResponse(BaseModel):
    id: str
    user_id: str
    url: str
    events: List[str]
    active: bool
    last_triggered: Optional[datetime]
    last_status: Optional[int]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookLogResponse(BaseModel):
    id: str
    webhook_id: str
    event: str
    payload: dict
    request_status: int
    request_error: Optional[str]
    attempts: int
    next_retry_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


async def verify_stripe_webhook(request: Request) -> bytes:
    """Validates Stripe webhooks to prevent forged payment confirmations."""
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Stripe signature",
        )

    payload = await request.body()
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook secret not configured",
        )

    try:
        stripe.Webhook.construct_event(payload, signature, secret)
    except ValueError:
        logger.warning("[WEBHOOK] Stripe payload verification failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe webhook payload",
        )
    except stripe.error.SignatureVerificationError:
        logger.warning("[WEBHOOK] Stripe signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Stripe webhook signature",
        )

    return payload


async def verify_generic_webhook(request: Request, secret_env_key: str) -> bytes:
    """Validates standard HMAC-SHA256 webhooks (e.g., custom third-party payloads)."""
    secret = os.getenv(secret_env_key, "").encode("utf-8")
    signature = request.headers.get("X-GraftAI-Signature")

    if not secret or not signature:
        logger.warning("[WEBHOOK] Missing generic webhook signature or secret")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook configuration",
        )

    payload = await request.body()
    expected_sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_sig, signature):
        logger.warning("[WEBHOOK] Generic webhook signature mismatch")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature mismatch",
        )

    return payload


@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await verify_stripe_webhook(request)
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON payload",
        )

    logger.info("[WEBHOOK] Verified Stripe webhook: %s", event.get("type"))
    return {"received": True, "event_type": event.get("type")}


@router.post("/custom")
async def custom_webhook(request: Request):
    payload = await verify_generic_webhook(request, "WEBHOOK_HMAC_SECRET")
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON payload",
        )

    logger.info(
        "[WEBHOOK] Verified custom webhook: id=%s type=%s",
        event.get("id"),
        event.get("type"),
    )
    safe_payload = {
        "id": event.get("id"),
        "type": event.get("type"),
    }
    return {"received": True, "payload": safe_payload}


@router.post("/google")
async def google_calendar_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handles Google Calendar push notifications.
    """
    resource_id = request.headers.get("X-Goog-Resource-ID")
    subscription_id = request.headers.get("X-Goog-Channel-ID")
    state = request.headers.get("X-Goog-Resource-State")
    channel_token = request.headers.get("X-Goog-Channel-Token", "")

    logger.info(
        f"[WEBHOOK] 📩 Google Notification: SubID={subscription_id}, State={state}"
    )

    if state == "sync":
        # Initial verification message, just return 200
        return Response(status_code=200)

    # Find the user associated with this subscription
    stmt = select(WebhookSubscriptionTable).where(
        WebhookSubscriptionTable.external_subscription_id == subscription_id
    )
    result = await db.execute(stmt)
    sub = result.scalars().first()

    # SEC-05: Verify the channel token matches the stored client_state
    if not sub or not hmac.compare_digest(sub.client_state or "", channel_token):
        logger.warning(
            f"[WEBHOOK] 🚨 Invalid or missing Google channel token for sub {subscription_id}"
        )
        return Response(status_code=403)

    # 1. Invalidate Cache
    await invalidate_user_calendar_cache(sub.user_id)
    await invalidate_user_calendar_busy_cache(sub.user_id)
    await invalidate_user_cache_pattern(sub.user_id, "availability")
    await invalidate_user_cache_pattern(sub.user_id, "busy_windows")
    # 2. Enqueue background sync with short debounce to avoid burst storms
    if await acquire_lock(f"webhook_sync_enqueue:{sub.user_id}", ttl_seconds=45):
        await enqueue_job("task_sync_calendar", user_id=sub.user_id)
        logger.info(f"[WEBHOOK] 🔄 Triggered background sync for user {sub.user_id}")
    else:
        logger.info(
            f"[WEBHOOK] ⏱ Debounced duplicate sync enqueue for user {sub.user_id}"
        )

    return Response(status_code=200)


@router.post("/microsoft")
async def microsoft_graph_webhook(
    request: Request, validationToken: str = None, db: AsyncSession = Depends(get_db)
):
    """
    Handles MS Graph push notifications.
    """
    # 1. Handle Validation Handshake
    if validationToken:
        logger.info("[WEBHOOK] 🛡️ MS Graph Validation Handshake received.")
        return Response(content=validationToken, media_type="text/plain")

    # 2. Handle Change Notification
    try:
        body = await request.json()
        notifications = body.get("value", [])

        for notif in notifications:
            sub_id = notif.get("subscriptionId")
            client_state = notif.get("clientState")

            stmt = select(WebhookSubscriptionTable).where(
                WebhookSubscriptionTable.external_subscription_id == sub_id
            )
            result = await db.execute(stmt)
            sub = result.scalars().first()

            if sub and sub.client_state == client_state:
                logger.info(f"[WEBHOOK] 🔄 MS Graph Change for user {sub.user_id}")
                await invalidate_user_calendar_cache(sub.user_id)
                await invalidate_user_calendar_busy_cache(sub.user_id)
                await invalidate_user_cache_pattern(sub.user_id, "availability")
                await invalidate_user_cache_pattern(sub.user_id, "busy_windows")
                if await acquire_lock(
                    f"webhook_sync_enqueue:{sub.user_id}", ttl_seconds=45
                ):
                    await enqueue_job("task_sync_calendar", user_id=sub.user_id)
                else:
                    logger.info(
                        f"[WEBHOOK] ⏱ Debounced duplicate sync enqueue for user {sub.user_id}"
                    )

    except Exception as e:
        logger.error(f"[WEBHOOK] ❌ Parse failure: {e}")

    return Response(status_code=202)


@router.get("/subscriptions", response_model=List[WebhookSubscriptionResponse])
async def list_subscriptions(
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_webhook_subscriptions(db, current_user.id)


@router.post("/subscriptions", response_model=WebhookSubscriptionResponse)
async def create_subscription(
    payload: WebhookSubscriptionPayload,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_webhook_subscription(
        db,
        current_user.id,
        payload.url,
        payload.events,
        payload.secret,
        active=payload.active,
    )


@router.patch("/subscriptions/{webhook_id}", response_model=WebhookSubscriptionResponse)
async def patch_subscription(
    webhook_id: str,
    payload: WebhookSubscriptionPayload,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    webhook = await update_webhook_subscription(
        db,
        current_user.id,
        webhook_id,
        url=payload.url,
        events=payload.events,
        secret=payload.secret,
        active=payload.active,
    )
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")
    return webhook


@router.delete("/subscriptions/{webhook_id}")
async def delete_subscription(
    webhook_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_webhook_subscription(db, current_user.id, webhook_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")
    return {"status": "deleted"}


@router.get("/subscriptions/{webhook_id}/logs", response_model=List[WebhookLogResponse])
async def get_subscription_logs(
    webhook_id: str,
    current_user: UserTable = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_webhook_logs(db, current_user.id, webhook_id)
