import hmac
import hashlib
import os
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable

router = APIRouter(prefix="/billing", tags=["billing"])

RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
if os.getenv("ENV", "development").lower() == "production" and not RAZORPAY_WEBHOOK_SECRET:
    import warnings
    warnings.warn("RAZORPAY_WEBHOOK_SECRET not set - Razorpay webhooks will fail verification")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

# Initialize Stripe
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

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


# Stripe Payment Integration

@router.post("/stripe/create-checkout-session")
async def create_stripe_checkout_session(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """
    Create a Stripe Checkout Session for subscription or one-time payment.
    """
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    try:
        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'GraftAI Pro Subscription',
                            'description': 'Monthly subscription with unlimited AI scheduling',
                        },
                        'unit_amount': 1900,  # $19.00 in cents
                        'recurring': {
                            'interval': 'month',
                        },
                    },
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard/settings/billing?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard/settings/billing?canceled=true",
            client_reference_id=current_user.id,
            metadata={
                'user_id': current_user.id,
                'user_email': current_user.email,
            }
        )
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stripe/create-portal-session")
async def create_stripe_portal_session(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """
    Create a Stripe Customer Portal session for managing subscriptions.
    """
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    if not current_user.razorpay_customer_id:  # Reuse this field for Stripe customer ID
        # Create a Stripe customer
        customer = stripe.Customer.create(
            email=current_user.email,
            name=current_user.full_name or current_user.email,
            metadata={'user_id': current_user.id}
        )
        current_user.razorpay_customer_id = customer.id
        await db.commit()
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.razorpay_customer_id,
            return_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard/settings/billing",
        )
        
        return {"portal_url": portal_session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhooks for subscription events.
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('metadata', {}).get('user_id')
        
        # Update user subscription status
        if user_id:
            # Find user by ID (simplified - in production use proper query)
            from sqlalchemy import select
            stmt = select(UserTable).where(UserTable.id == user_id)
            result = await db.execute(stmt)
            user = result.scalars().first()
            
            if user:
                user.tier = "pro"
                user.subscription_status = "active"
                user.razorpay_customer_id = session.get('customer')
                user.razorpay_subscription_id = session.get('subscription')
                user.daily_ai_limit = 200
                user.daily_sync_limit = 50
                user.trial_active = False
                await db.commit()
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        
        # Find user by customer ID
        from sqlalchemy import select
        stmt = select(UserTable).where(UserTable.razorpay_customer_id == customer_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if user:
            user.tier = "free"
            user.subscription_status = "canceled"
            user.razorpay_subscription_id = None
            user.daily_ai_limit = 10
            user.daily_sync_limit = 3
            await db.commit()
    
    elif event['type'] == 'invoice.payment_succeeded':
        # Payment succeeded - log for analytics
        pass
    
    elif event['type'] == 'invoice.payment_failed':
        # Payment failed - notify user
        pass
    
    return {"status": "success"}


@router.get("/stripe/config")
async def get_stripe_config():
    """
    Return Stripe publishable key for frontend initialization.
    """
    if not STRIPE_PUBLISHABLE_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    return {
        "publishable_key": STRIPE_PUBLISHABLE_KEY
    }

