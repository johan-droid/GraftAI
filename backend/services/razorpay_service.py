import os
import razorpay
import logging
import hmac
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import HTTPException, status
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
# These should be created in the Razorpay Dashboard beforehand
RZP_PLAN_PRO = os.getenv("RAZORPAY_PLAN_PRO_ID")
RZP_PLAN_ELITE = os.getenv("RAZORPAY_PLAN_ELITE_ID")

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
        # Create Subscription
        # Note: total_count=12 for a year, or we can leave it for indefinite
        subscription = client.subscription.create({
            "plan_id": plan_id,
            "customer_notify": 1,
            "total_count": 120, # 10 years of monthly billing
            "notes": {
                "user_id": user_id,
                "tier": tier
            }
        })
        
        # Update user with RZP subscription ID (preliminary)
        async with db.begin():
            user.razorpay_subscription_id = subscription["id"]
        
        return subscription
    except Exception as e:
        logger.error(f"Razorpay Subscription creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create Razorpay subscription")

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

    # 3. Log as processed
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
    
    return {"status": "success"}

async def _handle_subscription_activated(db: AsyncSession, subscription: Dict[str, Any]):
    sub_id = subscription.get("id")
    # We can also use notes if available in the webhook payload
    user_id = subscription.get("notes", {}).get("user_id")
    tier = subscription.get("notes", {}).get("tier", UserTier.PRO)

    async with db.begin():
        # Find user by subscription ID
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
    
    async with db.begin():
        result = await db.execute(select(UserTable).where(UserTable.razorpay_subscription_id == sub_id))
        user = result.scalars().first()
        if user:
            user.subscription_status = "canceled"
            user.tier = UserTier.FREE
            logger.info(f"🗑 User {user.id} Razorpay subscription canceled, reverted to FREE")
