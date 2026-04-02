import os
import logging
from typing import Optional, Dict, Any

try:
    import stripe
except ImportError:
    stripe = None
    logging.getLogger(__name__).warning("Stripe package not installed; billing endpoints degraded.")
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.tables import UserTable, UserTier

logger = logging.getLogger(__name__)

# Stripe Configuration
if stripe is not None:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")

# Price IDs (Should be in .env)
STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO_ID")
STRIPE_PRICE_ELITE = os.getenv("STRIPE_PRICE_ELITE_ID")

async def create_checkout_session(db: AsyncSession, user_id: str, tier: str) -> str:
    """Create a Stripe Checkout session for a specific tier."""
    if stripe is None:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    price_id = STRIPE_PRICE_PRO if tier == "pro" else STRIPE_PRICE_ELITE
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Invalid or unconfigured tier: {tier}")

    try:
        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            customer_email=user.email if not user.stripe_customer_id else None,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{FRONTEND_URL}/dashboard/settings/billing?success=true",
            cancel_url=f"{FRONTEND_URL}/dashboard/settings/billing?canceled=true",
            metadata={"user_id": user_id, "tier": tier},
        )
        return checkout_session.url
    except Exception as e:
        logger.error(f"Stripe Checkout error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

async def create_portal_session(db: AsyncSession, user_id: str) -> str:
    """Create a Stripe Customer Portal session for subscription management."""
    if stripe is None:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    result = await db.execute(select(UserTable).where(UserTable.id == user_id))
    user = result.scalars().first()
    
    if not user or not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="User does not have a billing profile")

    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=f"{FRONTEND_URL}/dashboard/settings/billing",
        )
        return portal_session.url
    except Exception as e:
        logger.error(f"Stripe Portal error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")

async def handle_webhook_event(db: AsyncSession, payload: bytes, sig_header: str):
    """Handle incoming Stripe webhook events with idempotency check."""
    if stripe is None:
        raise HTTPException(status_code=503, detail="Stripe is not configured")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {sig_header[:10]}... Error: {e}")
        raise ValueError("Invalid signature")

    event_id = event["id"]
    from backend.models.tables import ProcessedWebhook
    
    # 1. Check for duplicate webhook events
    result = await db.execute(select(ProcessedWebhook).where(ProcessedWebhook.event_id == event_id))
    if result.scalars().first():
        logger.warning(f"⏩ Skipping already processed Stripe event: {event_id}")
        return {"status": "already_processed"}

    event_type = event["type"]
    data_object = event["data"]["object"]

    # 2. Process and Record (Atomic within caller or handled by internal begins)
    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(db, data_object)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(db, data_object)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(db, data_object)
    
    # 3. Log as processed
    db.add(ProcessedWebhook(event_id=event_id, provider="stripe"))
    await db.commit()
    
    return {"status": "success"}

async def _handle_checkout_completed(db: AsyncSession, session: Dict[str, Any]):
    user_id = session.get("metadata", {}).get("user_id")
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    
    if not user_id: return

    async with db.begin():
        result = await db.execute(select(UserTable).where(UserTable.id == user_id))
        user = result.scalars().first()
        if user:
            user.stripe_customer_id = customer_id
            user.subscription_status = "active"
            user.tier = session.get("metadata", {}).get("tier", UserTier.PRO)
            logger.info(f"✅ User {user_id} upgraded to {user.tier}")

async def _handle_subscription_updated(db: AsyncSession, subscription: Dict[str, Any]):
    customer_id = subscription.get("customer")
    status = subscription.get("status")
    
    async with db.begin():
        result = await db.execute(select(UserTable).where(UserTable.stripe_customer_id == customer_id))
        user = result.scalars().first()
        if user:
            user.subscription_status = status
            # Logic for tier mapping based on plan ID could be added here
            logger.info(f"🔄 User {user.id} subscription status updated to {status}")

async def _handle_subscription_deleted(db: AsyncSession, subscription: Dict[str, Any]):
    customer_id = subscription.get("customer")
    
    async with db.begin():
        result = await db.execute(select(UserTable).where(UserTable.stripe_customer_id == customer_id))
        user = result.scalars().first()
        if user:
            user.subscription_status = "canceled"
            user.tier = UserTier.FREE
            logger.info(f"🗑 User {user.id} subscription canceled, reverted to FREE")
