from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.utils.db import get_db
from backend.auth.schemes import get_current_user_id
from backend.services import billing, razorpay_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

@router.post("/checkout-session")
async def create_checkout(
    tier: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Start a checkout session for a specific tier."""
    session_url = await billing.create_checkout_session(db, user_id, tier)
    return {"url": session_url}

@router.post("/portal-session")
async def create_portal(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Start a customer portal session for management."""
    portal_url = await billing.create_portal_session(db, user_id)
    return {"url": portal_url}

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle incoming Stripe events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature")
    
    try:
        return await billing.handle_webhook_event(db, payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal webhook processing error")

@router.post("/razorpay/create-subscription")
async def rzp_create_subscription(
    tier: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Start a Razorpay subscription for a specific tier."""
    subscription = await razorpay_service.create_subscription(db, user_id, tier)
    return subscription


@router.get("/razorpay/public-key")
async def rzp_public_key(
    user_id: str = Depends(get_current_user_id)
):
    """Fetch the public Razorpay key ID (safe to expose)."""
    key_id = razorpay_service.RAZORPAY_KEY_ID
    if not key_id:
        raise HTTPException(status_code=500, detail="Razorpay public key is not configured")
    return {"key_id": key_id}

@router.post("/razorpay/webhook")
async def rzp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle incoming Razorpay events."""
    payload = await request.body()
    sig_header = request.headers.get("x-razorpay-signature")
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing x-razorpay-signature")
    
    if not razorpay_service.verify_webhook_signature(payload, sig_header):
        raise HTTPException(status_code=400, detail="Invalid Razorpay signature")
    
    import json
    try:
        event_data = json.loads(payload)
        return await razorpay_service.handle_webhook_event(db, event_data)
    except Exception as e:
        logger.error(f"Razorpay webhook error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process Razorpay webhook")
