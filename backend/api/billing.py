import hmac
import hashlib
import logging
import os
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import stripe
import razorpay

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable, ManualActivationRequestTable, AuditLogTable
from backend.auth.schemes import require_admin
from pydantic import BaseModel
from datetime import datetime, timezone
from backend.services.mail_service import send_email
from pathlib import Path
import uuid

router = APIRouter(prefix="/billing", tags=["billing"])
logger = logging.getLogger(__name__)

# Environment detection for simulation endpoints
ENV = os.getenv("ENV", "development").lower()
IS_PRODUCTION = ENV == "production"

# Payment mode controls whether real gateways are used, sandbox simulation is allowed,
# or payments are disabled entirely. Values: 'disabled' | 'test' | 'production'
PAYMENT_MODE = os.getenv("PAYMENT_MODE", "test" if ENV != "production" else "production").lower()
if PAYMENT_MODE not in {"disabled", "test", "production"}:
    PAYMENT_MODE = "test" if ENV != "production" else "production"

# Convenience flag for allowing simulated checkout/verify endpoints
CAN_SIMULATE = PAYMENT_MODE == "test"

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


@router.get("/mode")
async def get_billing_mode():
    """Return the effective payment mode and available gateways for frontend display."""
    return {
        "payment_mode": PAYMENT_MODE,
        "can_simulate": CAN_SIMULATE,
        "gateways": {
            "razorpay": bool(os.getenv("RAZORPAY_KEY_ID") and os.getenv("RAZORPAY_KEY_SECRET")),
            "stripe": bool(STRIPE_SECRET_KEY),
        },
        "is_production": IS_PRODUCTION,
    }

@router.post("/razorpay/checkout")
async def create_checkout_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """
    Create Razorpay Checkout Session.
    
    In production: Returns real order from Razorpay API
    In development: Returns simulated order for testing
    """
    # Attempt to read the requested tier from the body (optional)
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    tier = str(payload.get("tier", "pro")).lower()

    # Map tiers to INR prices (in paise) for Razorpay
    razorpay_tier_amounts = {
        "pro": 49900,   # ₹499.00
        "elite": 149900 # ₹1499.00
    }

    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
    # If payments are disabled for this deployment, return a descriptive response
    if PAYMENT_MODE == "disabled":
        return {
            "mode": "disabled",
            "message": "Payments are disabled for this deployment. Please request an upgrade from the account owner.",
        }

    # If Razorpay keys are present, create a real Razorpay order
    if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
        try:
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
            amount = razorpay_tier_amounts.get(tier, 49900)
            # Create order in paise
            order = client.order.create({
                "amount": amount,
                "currency": "INR",
                "receipt": f"rcpt_{current_user.id[:8]}_{tier}",
                "notes": {"user_id": current_user.id, "tier": tier},
            })

            return {
                "order_id": order.get("id"),
                "key": RAZORPAY_KEY_ID,
                "amount": order.get("amount"),
                "currency": order.get("currency", "INR"),
                "mode": "razorpay",
            }
        except Exception as e:
            logger.exception("Failed to create Razorpay order")
            raise HTTPException(status_code=500, detail="Failed to create Razorpay order")

    # Fallback when no keys are configured
    if PAYMENT_MODE == "test":
        return {
            "order_id": "order_simulated_" + current_user.id[:8],
            "key": os.getenv("RAZORPAY_KEY_ID", "rzp_test_dummy"),
            "amount": 1900,
            "currency": "USD",
            "mode": "simulation",
            "warning": "This is a simulated checkout. No real payment will be processed."
        }

    # If not test mode and no keys, payments are effectively disabled
    return {
        "mode": "disabled",
        "message": "Payments are not configured for this deployment. Please contact the account owner to enable payments.",
    }

@router.post("/razorpay/verify-simulation")
async def simulate_verification(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """
    Simulate successful payment and subscription upgrade for Demo.
    
    WARNING: This endpoint is BLOCKED in production to prevent unauthorized upgrades.
    It is only available in development environment for testing purposes.
    """
    # Block simulation unless running in allowed test mode
    if not CAN_SIMULATE:
        try:
            anonymized_id = hashlib.sha256(current_user.id.encode("utf-8")).hexdigest()[:8]
        except Exception:
            anonymized_id = "unknown"
        logger.error(f"🚫 BLOCKED: Attempt to use simulation endpoint when PAYMENT_MODE={PAYMENT_MODE} by user_id_hash={anonymized_id}")
        raise HTTPException(
            status_code=403,
            detail="Simulation endpoints are not available in this environment. Please use real payment flows or request manual activation."
        )
    
    data = await request.json()
    if not data.get("razorpay_payment_id"):
        raise HTTPException(status_code=400, detail="Invalid payment details")

    # Log simulation usage for audit trail (anonymized)
    try:
        sim_id_hash = hashlib.sha256(current_user.id.encode("utf-8")).hexdigest()[:8]
    except Exception:
        sim_id_hash = "unknown"
    logger.warning(f"⚠️  SIMULATION: user_id_hash={sim_id_hash} using verify-simulation endpoint")
    
    current_user.tier = "pro"
    current_user.subscription_status = "active"
    current_user.razorpay_subscription_id = f"sub_sim_{current_user.id[:8]}"
    current_user.daily_ai_limit = 200
    current_user.daily_sync_limit = 50
    current_user.trial_active = False

    await db.commit()
    await db.refresh(current_user)

    return {
        "status": "success",
        "message": "Subscription upgraded to Pro (SIMULATION MODE - NOT A REAL PAYMENT)",
        "mode": "simulation",
        "warning": "This is a test upgrade. No actual payment was processed."
    }

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
        # Return 403 to signal Razorpay to retry - returning 200 would confirm receipt
        # and prevent retries, potentially causing missed webhook events
        logger.warning(f"❌ Invalid Razorpay webhook signature from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=403,
            detail="Invalid webhook signature"
        )

    try:
        event = json.loads(body)
        evt_type = event.get("event")
        payload = event.get("payload", {})
        
        if evt_type == "subscription.activated" or evt_type == "subscription.charged":
            pass
            
    except Exception as e:
        print(f"Webhook error: {e}")
        
    return {"status": "processed"}


@router.post("/razorpay/verify")
async def verify_razorpay_payment(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """
    Verify Razorpay payment signature after checkout and activate subscription.
    Expects JSON: { razorpay_payment_id, razorpay_order_id, razorpay_signature }
    """
    data = await request.json()
    payment_id = data.get("razorpay_payment_id")
    order_id = data.get("razorpay_order_id")
    signature = data.get("razorpay_signature")

    if not (payment_id and order_id and signature):
        raise HTTPException(status_code=400, detail="Missing payment verification fields")
    # Do not allow verification when payments are explicitly disabled
    if PAYMENT_MODE == "disabled":
        raise HTTPException(status_code=403, detail="Payments are disabled for this deployment; cannot verify payments")

    # If no secret configured but we're in test mode, accept simulated verification
    if not RAZORPAY_KEY_SECRET:
        if PAYMENT_MODE == "test":
            logger.info("Razorpay secret not configured: accepting simulated verification in test mode for order %s", order_id)
            # Skip signature verification in test mode (simulation)
        else:
            raise HTTPException(status_code=500, detail="Razorpay secret not configured")
    else:
        # Verify signature according to Razorpay docs
        computed = hmac.new(RAZORPAY_KEY_SECRET.encode("utf-8"), f"{order_id}|{payment_id}".encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, signature):
            logger.warning("Invalid Razorpay signature for order %s", order_id)
            raise HTTPException(status_code=403, detail="Invalid signature")

    # Fetch order info (optional) to retrieve notes like tier
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    tier = "pro"
    try:
        if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
            order = client.order.fetch(order_id)
            tier = order.get("notes", {}).get("tier", "pro")
    except Exception:
        # Non-fatal - continue with default tier
        logger.exception("Could not fetch Razorpay order to determine tier")

    # Before activating, verify the payment status with Razorpay (must be 'captured')
    if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
        try:
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
            payment = client.payment.fetch(payment_id)
            payment_status = payment.get("status")
            if payment_status != "captured":
                logger.warning("Razorpay payment not captured: %s (status=%s)", payment_id, payment_status)
                raise HTTPException(status_code=400, detail="Payment not captured; subscription not activated")
        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to verify Razorpay payment %s", payment_id)
            raise HTTPException(status_code=500, detail="Failed to verify payment with Razorpay")

    # Activate subscription for user (only after successful capture verification)
    current_user.tier = tier
    current_user.subscription_status = "active"
    current_user.razorpay_subscription_id = payment_id

    # Quota defaults for tiers
    if tier == "elite":
        current_user.daily_ai_limit = 2000
        current_user.daily_sync_limit = 500
    elif tier == "pro":
        current_user.daily_ai_limit = 200
        current_user.daily_sync_limit = 50
    else:
        current_user.daily_ai_limit = 10
        current_user.daily_sync_limit = 3

    await db.commit()
    await db.refresh(current_user)

    return {"status": "success", "tier": tier}


# Presigned upload helper for manual proof uploads
class PresignRequest(BaseModel):
    filename: str
    content_type: str | None = None


@router.post("/manual/presign")
async def presign_manual_upload(
    payload: PresignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Return a presigned upload URL (or backend upload fallback) for manual proof files."""
    from backend.services.storage import storage

    extension = Path(payload.filename).suffix or ".dat"
    secure_filename = f"{uuid.uuid4()}{extension}"
    remote_path = f"{current_user.id}/{secure_filename}"

    presign = storage.get_presigned_upload_url(remote_path, content_type=payload.content_type)
    if not presign:
        raise HTTPException(status_code=500, detail="Could not generate presigned upload URL")

    return presign


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
    
    if not current_user.stripe_customer_id:
        # Create a Stripe customer
        customer = stripe.Customer.create(
            email=current_user.email,
            name=current_user.full_name or current_user.email,
            metadata={'user_id': current_user.id}
        )
        current_user.stripe_customer_id = customer.id
        await db.commit()
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
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
            # Find user by ID
            stmt = select(UserTable).where(UserTable.id == user_id)
            result = await db.execute(stmt)
            user = result.scalars().first()
            
            if user:
                user.tier = "pro"
                user.subscription_status = "active"
                # SECURITY: Use separate columns for Stripe customer/subscription IDs
                user.stripe_customer_id = session.get('customer')
                user.stripe_subscription_id = session.get('subscription')
                user.daily_ai_limit = 200
                user.daily_sync_limit = 50
                user.trial_active = False
                await db.commit()
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        
        # Find user by Stripe customer ID (not Razorpay)
        # SECURITY: Stripe webhook uses stripe_customer_id column
        stmt = select(UserTable).where(UserTable.stripe_customer_id == customer_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if user:
            user.tier = "free"
            user.subscription_status = "canceled"
            # Clear Stripe subscription ID
            user.stripe_subscription_id = None
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


# -----------------------------
# Manual Activation (Admin) APIs
# -----------------------------


class ManualActivationCreate(BaseModel):
    requested_tier: str = "pro"
    proof_key: str | None = None
    proof_url: str | None = None
    notes: str | None = None


class ManualActivationAdminNotes(BaseModel):
    admin_notes: str | None = None


@router.post("/manual/request")
async def create_manual_activation_request(
    payload: ManualActivationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """Create a manual activation request (used when payments are not available).

    The request remains in `pending` state until an admin approves or rejects it.
    """
    req = ManualActivationRequestTable(
        user_id=current_user.id,
        requested_tier=payload.requested_tier or "pro",
        proof_url=payload.proof_key or payload.proof_url,
        notes=payload.notes,
        status="pending",
    )

    db.add(req)
    await db.commit()
    await db.refresh(req)

    # Create audit entry
    try:
        email_hash = None
        if current_user.email:
            email_hash = hashlib.sha256(current_user.email.encode("utf-8")).hexdigest()

        audit = AuditLogTable(
            event_type="manual_activation_request",
            event_category="billing",
            severity="info",
            user_id=current_user.id,
            user_email=email_hash,
            action="create",
            resource_type="manual_activation_request",
            resource_id=req.id,
            result="success",
        )
        db.add(audit)
        await db.commit()
    except Exception:
        logger.exception("Failed to create audit log for manual activation request")

    # Send admin notification email (best-effort)
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@graftai.com")
        frontend_base = os.getenv("FRONTEND_BASE_URL", os.getenv("FRONTEND_URL", "http://localhost:3000")).rstrip("/")
        review_link = f"{frontend_base}/dashboard/admin/manual-requests"
        subject = f"[Manual Activation] Request {req.id}"
        html_body = (
            f"<p>Manual activation request <strong>{req.id}</strong> has been created.</p>"
            f"<p>User: <strong>{current_user.email or current_user.id}</strong></p>"
            f"<p>Requested tier: <strong>{req.requested_tier}</strong></p>"
            f"<p>Notes: {req.notes or ''}</p>"
            f"<p>Proof: <a href=\"{req.proof_url or review_link}\">View proof / review</a></p>"
            f"<p><a href=\"{review_link}\">Open admin review</a></p>"
        )
        text_body = (
            f"Manual activation request {req.id} has been created.\n"
            f"User: {current_user.email or current_user.id}\n"
            f"Requested tier: {req.requested_tier}\n"
            f"Review: {review_link}\n"
            f"Notes: {req.notes or ''}"
        )
        await send_email(admin_email, subject, html_body, text_body)
    except Exception as e:
        logger.warning("Failed to send admin notification for manual activation: %s", e)

    return {"status": "success", "request_id": req.id}


@router.get("/manual/requests")
async def list_manual_activation_requests(
    status: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _admin_id: str = Depends(require_admin),
):
    """List manual activation requests. Admin only."""
    stmt = select(ManualActivationRequestTable).order_by(ManualActivationRequestTable.created_at.desc())
    if status:
        stmt = stmt.where(ManualActivationRequestTable.status == status)
    stmt = stmt.limit(min(1000, max(1, limit)))
    results = (await db.execute(stmt)).scalars().all()

    def serialize(r: ManualActivationRequestTable) -> dict:
        return {
            "id": r.id,
            "user_id": r.user_id,
            "requested_tier": r.requested_tier,
            "proof_url": r.proof_url,
            "notes": r.notes,
            "admin_notes": r.admin_notes,
            "status": r.status,
            "reviewed_by": r.reviewed_by,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }

    return [serialize(r) for r in results]


@router.post("/manual/requests/{request_id}/approve")
async def approve_manual_activation_request(
    request_id: str,
    payload: ManualActivationAdminNotes | None = None,
    db: AsyncSession = Depends(get_db),
    admin_id: str = Depends(require_admin),
):
    """Approve a pending manual activation request (admin only)."""
    req = await db.get(ManualActivationRequestTable, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Request is not pending")

    user = await db.get(UserTable, req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Approve and apply tier/quotas
    req.status = "approved"
    req.reviewed_by = admin_id
    req.reviewed_at = datetime.now(timezone.utc)
    if payload and payload.admin_notes:
        req.admin_notes = payload.admin_notes

    user.tier = req.requested_tier
    user.subscription_status = "active"
    user.trial_active = False
    if req.requested_tier == "elite":
        user.daily_ai_limit = 2000
        user.daily_sync_limit = 500
    elif req.requested_tier == "pro":
        user.daily_ai_limit = 200
        user.daily_sync_limit = 50
    else:
        user.daily_ai_limit = 10
        user.daily_sync_limit = 3

    await db.commit()

    if user.email:
        try:
            frontend_base = os.getenv("FRONTEND_BASE_URL", os.getenv("FRONTEND_URL", "http://localhost:3000")).rstrip("/")
            support_link = f"{frontend_base}/support"
            subject = f"[Manual Activation Approved] Request {req.id}"
            html_body = (
                f"<p>Your manual activation request <strong>{req.id}</strong> has been <strong>approved</strong>.</p>"
                f"<p>New tier: <strong>{req.requested_tier}</strong></p>"
                f"<p>Admin notes: <em>{req.admin_notes or 'None'}</em></p>"
                f"<p>If you have questions, please contact support: <a href=\"{support_link}\">{support_link}</a></p>"
            )
            text_body = (
                f"Your manual activation request {req.id} has been approved.\n"
                f"New tier: {req.requested_tier}\n"
                f"Admin notes: {req.admin_notes or 'None'}\n"
                f"Contact support: {support_link}"
            )
            await send_email(user.email, subject, html_body, text_body)
        except Exception:
            logger.exception("Failed to send manual activation approval email for request %s", req.id)

    return {"status": "success", "request_id": req.id}


@router.post("/manual/requests/{request_id}/reject")
async def reject_manual_activation_request(
    request_id: str,
    payload: ManualActivationAdminNotes | None = None,
    db: AsyncSession = Depends(get_db),
    admin_id: str = Depends(require_admin),
):
    """Reject a pending manual activation request (admin only)."""
    req = await db.get(ManualActivationRequestTable, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Request is not pending")

    req.status = "rejected"
    req.reviewed_by = admin_id
    req.reviewed_at = datetime.now(timezone.utc)
    if payload and payload.admin_notes:
        req.admin_notes = payload.admin_notes

    await db.commit()

    if user := await db.get(UserTable, req.user_id):
        if user.email:
            try:
                frontend_base = os.getenv("FRONTEND_BASE_URL", os.getenv("FRONTEND_URL", "http://localhost:3000")).rstrip("/")
                support_link = f"{frontend_base}/support"
                subject = f"[Manual Activation Rejected] Request {req.id}"
                html_body = (
                    f"<p>Your manual activation request <strong>{req.id}</strong> has been <strong>rejected</strong>.</p>"
                    f"<p>Requested tier: <strong>{req.requested_tier}</strong></p>"
                    f"<p>Reason: <em>{req.admin_notes or 'No additional notes provided.'}</em></p>"
                    f"<p>Please contact support to discuss next steps: <a href=\"{support_link}\">{support_link}</a></p>"
                )
                text_body = (
                    f"Your manual activation request {req.id} has been rejected.\n"
                    f"Requested tier: {req.requested_tier}\n"
                    f"Reason: {req.admin_notes or 'No additional notes provided.'}\n"
                    f"Contact support: {support_link}"
                )
                await send_email(user.email, subject, html_body, text_body)
            except Exception:
                logger.exception("Failed to send manual activation rejection email for request %s", req.id)

    return {"status": "success", "request_id": req.id}

