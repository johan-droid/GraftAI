import os
import razorpay
import logging
import hmac
import hashlib
from typing import Dict, Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.tables import UserTable, UserTier

logger = logging.getLogger(__name__)

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Plan IDs (Should be in .env)
RZP_PLAN_PRO = os.getenv("RAZORPAY_PLAN_PRO_ID")
RZP_PLAN_ELITE = os.getenv("RAZORPAY_PLAN_ELITE_ID")

async def _ensure_customer(db: AsyncSession, user: UserTable) -> str:
    """Ensure the user has a Razorpay customer record."""
    if user.razorpay_customer_id:
        return user.razorpay_customer_id

    try:
        customer = client.customer.create({
            "name": user.name or user.full_name or user.email,
            "email": user.email,
            "contact": "",
            "notes": {"user_id": user.id}
        })
        user.razorpay_customer_id = customer.get("id")
        await db.commit()
        return user.razorpay_customer_id
    except Exception as e:
        logger.error(f"Razorpay customer creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Razorpay customer")

async def create_subscription(db: AsyncSession, user_id: str, tier: str) -> Dict[str, Any]:
    """Create a Razorpay Subscription for a specific tier."""
    if not client:
        raise HTTPException(status_code=500, detail="Razorpay is not configured")

    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan_id = RZP_PLAN_PRO if tier == "pro" else RZP_PLAN_ELITE
    if not plan_id:
        raise HTTPException(status_code=400, detail=f"Invalid or unconfigured Razorpay tier: {tier}")

    try:
        razorpay_customer_id = await _ensure_customer(db, user)

        subscription = client.subscription.create({
            "plan_id": plan_id,
            "customer_notify": 1,
            "customer_id": razorpay_customer_id,
            "notes": {
                "user_id": user_id,
                "tier": tier
            }
        })

        user.razorpay_subscription_id = subscription["id"]
        if subscription.get("customer_id"):
            user.razorpay_customer_id = subscription.get("customer_id")
        await db.commit()

        return {
            "id": subscription["id"],
            "status": subscription.get("status"),
            "plan_id": subscription.get("plan_id"),
            "short_url": subscription.get("short_url")
        }
    except Exception as e:
        logger.error(f"Razorpay Subscription creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Razorpay subscription")

async def get_subscription_status(db: AsyncSession, user_id: str) -> Dict[str, Any] | None:
    """Fetch current Razorpay subscription details for the logged-in user."""
    if not client:
        raise HTTPException(status_code=500, detail="Razorpay is not configured")

    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()
    if not user or not user.razorpay_subscription_id:
        return None

    try:
        subscription = client.subscription.fetch(user.razorpay_subscription_id)
        return {
            "id": subscription.get("id"),
            "status": subscription.get("status"),
            "plan_id": subscription.get("plan_id"),
            "customer_id": subscription.get("customer_id"),
            "current_start": subscription.get("current_start"),
            "current_end": subscription.get("current_end"),
            "notes": subscription.get("notes", {})
        }
    except Exception as e:
        logger.error(f"Razorpay subscription fetch error: {e}")
        return None

async def cancel_subscription(db: AsyncSession, user_id: str) -> Dict[str, Any]:
    """Cancel an active Razorpay subscription immediately."""
    if not client:
        raise HTTPException(status_code=500, detail="Razorpay is not configured")

    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()
    if not user or not user.razorpay_subscription_id:
        raise HTTPException(status_code=404, detail="No active Razorpay subscription found")

    try:
        cancellation = client.subscription.cancel(user.razorpay_subscription_id, {"cancel_at_cycle_end": 0})
        user.subscription_status = "canceled"
        user.tier = UserTier.FREE
        await db.commit()
        return {
            "status": "canceled",
            "subscription_id": user.razorpay_subscription_id,
            "razorpay_response": cancellation
        }
    except Exception as e:
        logger.error(f"Razorpay subscription cancellation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel Razorpay subscription")

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify the signature of an incoming Razorpay webhook."""
    if not RAZORPAY_WEBHOOK_SECRET:
        return False

    try:
        expected_signature = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Razorpay Webhook signature verification failed: {e}")
        return False

async def handle_webhook_event(db: AsyncSession, event_data: Dict[str, Any]):
    """Handle incoming Razorpay webhook events with idempotency check."""
    event_id = event_data.get("id")
    if not event_id:
        logger.warning("Razorpay webhook missing ID, skipping idempotency check.")
        return await _process_razorpay_event(db, event_data)

    from backend.models.tables import ProcessedWebhook

    # 1. Check for duplicate webhook events
    result = await db.execute(select(ProcessedWebhook).where(ProcessedWebhook.event_id == event_id))
    if result.scalars().first():
        logger.warning(f"⏩ Skipping already processed Razorpay event: {event_id}")
        return {"status": "already_processed"}

    # 2. Process event
    response = await _process_razorpay_event(db, event_data)

    # 3. Log as processed and commit once
    db.add(ProcessedWebhook(event_id=event_id, provider="razorpay"))
    await db.commit()

    return response

async def _process_razorpay_event(db: AsyncSession, event_data: Dict[str, Any]):
    """Internal helper to route the actual Razorpay event type."""
    event_type = event_data.get("event")
    payload = event_data.get("payload", {})

    if event_type == "subscription.activated":
        await _handle_subscription_activated(db, payload.get("subscription", {}).get("entity", {}))
    elif event_type in ("subscription.halted", "subscription.cancelled"):
        await _handle_subscription_cancelled(db, payload.get("subscription", {}).get("entity", {}))
    elif event_type == "payment.failed":
        await _handle_payment_failed(db, payload.get("payment", {}).get("entity", {}))

    return {"status": "success"}

async def _handle_subscription_activated(db: AsyncSession, subscription: Dict[str, Any]):
    sub_id = subscription.get("id")
    user_id = subscription.get("notes", {}).get("user_id")
    tier = subscription.get("notes", {}).get("tier", UserTier.PRO)

    result = await db.execute(select(UserTable).where(UserTable.razorpay_subscription_id == sub_id))
    user = result.scalars().first()

    if not user and user_id:
        result = await db.execute(select(UserTable).where(UserTable.id == user_id))
        user = result.scalars().first()

    if user:
        user.razorpay_subscription_id = sub_id
        user.subscription_status = "active"
        user.tier = tier
        logger.info(f"✅ User {user.id} upgraded to {tier} via Razorpay")

async def _handle_subscription_cancelled(db: AsyncSession, subscription: Dict[str, Any]):
    sub_id = subscription.get("id")

    result = await db.execute(select(UserTable).where(UserTable.razorpay_subscription_id == sub_id))
    user = result.scalars().first()
    if user:
        user.subscription_status = "canceled"
        user.tier = UserTier.FREE
        logger.info(f"🗑 User {user.id} Razorpay subscription canceled, reverted to FREE")

async def _handle_payment_failed(db: AsyncSession, payment: Dict[str, Any]):
    sub_id = payment.get("subscription_id")
    if not sub_id:
        return

    result = await db.execute(select(UserTable).where(UserTable.razorpay_subscription_id == sub_id))
    user = result.scalars().first()
    if user:
        user.subscription_status = "past_due"
        logger.warning(f"⚠️ User {user.id} Razorpay payment failed, marking subscription as past_due")