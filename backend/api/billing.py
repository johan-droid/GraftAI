import hmac
import hashlib
import os
import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable

router = APIRouter(prefix="/billing", tags=["billing"])

RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "dummy_webhook_secret")

def verify_razorpay_signature(body: bytes, signature: str, secret: str) -> bool:
    try:
        expected = hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False

@router.post("/razorpay/checkout")
async def create_checkout_session(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """
    Simulated Razorpay Checkout Initiation 
    In production, this returns a razorpay order_id.
    """
    return {
        "order_id": "order_simulated_" + current_user.id[:8],
        "key": os.getenv("RAZORPAY_KEY_ID", "rzp_test_dummy"),
        "amount": 1900,
        "currency": "USD"
    }

@router.post("/razorpay/verify-simulation")
async def simulate_verification(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """
    Simulate successful payment and subscription upgrade for Demo.
    """
    data = await request.json()
    if not data.get("razorpay_payment_id"):
        raise HTTPException(status_code=400, detail="Invalid payment details")

    current_user.tier = "pro"
    current_user.subscription_status = "active"
    current_user.razorpay_subscription_id = f"sub_sim_{current_user.id[:8]}"
    current_user.daily_ai_limit = 200
    current_user.daily_sync_limit = 50
    current_user.trial_active = False

    await db.commit()
    await db.refresh(current_user)

    return {"status": "success", "message": "Subscription upgraded to Pro"}

@router.post("/razorpay/cancel-subscription")
async def cancel_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    if not current_user.razorpay_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription found.")

    # We will simulate successful cancellation for now
    current_user.tier = "free"
    current_user.subscription_status = "canceled"
    current_user.razorpay_subscription_id = None
    
    # Revert quota limits
    current_user.daily_ai_limit = 10
    current_user.daily_sync_limit = 3
    
    await db.commit()
    return {"status": "success", "message": "Subscription cancelled and tier reverted to free."}

@router.post("/razorpay/webhook")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature")
    
    if not signature or not verify_razorpay_signature(body, signature, RAZORPAY_WEBHOOK_SECRET):
        # We log and ignore invalid webhook signatures
        return {"status": "ignored", "message": "Invalid signature"}

    try:
        event = json.loads(body)
        evt_type = event.get("event")
        payload = event.get("payload", {})
        
        if evt_type == "subscription.activated" or evt_type == "subscription.charged":
            pass
            
    except Exception as e:
        print(f"Webhook error: {e}")
        
    return {"status": "processed"}
