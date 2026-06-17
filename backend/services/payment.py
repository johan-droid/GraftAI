import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.redis import publish_message
from backend.models.tables import BookingTable, PaymentIntentTable, UserTable
from backend.services.usage import build_quota_snapshot

logger = logging.getLogger(__name__)

TIER_LIMITS: dict[str, dict[str, int]] = {
    "free": {"daily_ai_limit": 10, "daily_sync_limit": 3},
    "pro": {"daily_ai_limit": 200, "daily_sync_limit": 50},
    "elite": {"daily_ai_limit": 2000, "daily_sync_limit": 500},
}


async def create_payment_intent(
    db: AsyncSession,
    user_id: str,
    gateway: str,
    amount: float,
    currency: str,
    booking_id: str | None = None,
    event_type_id: str | None = None,
    metadata_payload: dict | None = None,
) -> PaymentIntentTable:
    intent = PaymentIntentTable(
        user_id=user_id,
        booking_id=booking_id,
        event_type_id=event_type_id,
        gateway=gateway,
        gateway_payment_intent_id=None,
        amount=amount,
        currency=currency,
        status="initiated",
        metadata_payload=metadata_payload or {},
    )
    db.add(intent)
    await db.flush()
    await db.refresh(intent)
    return intent


async def update_payment_intent_gateway_id(
    db: AsyncSession,
    intent_id: str,
    gateway_payment_intent_id: str,
    client_secret: str | None = None,
) -> PaymentIntentTable | None:
    intent = await db.get(PaymentIntentTable, intent_id)
    if not intent:
        logger.warning("PaymentIntent %s not found for gateway ID update", intent_id)
        return None
    intent.gateway_payment_intent_id = gateway_payment_intent_id
    intent.client_secret = client_secret
    intent.status = "requires_confirmation"
    await db.flush()
    await db.refresh(intent)
    return intent


async def _apply_tier_upgrade(user: UserTable, tier: str) -> None:
    user.tier = tier
    user.subscription_status = "active"
    user.trial_active = False
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    user.daily_ai_limit = limits["daily_ai_limit"]
    user.daily_sync_limit = limits["daily_sync_limit"]


async def confirm_payment_intent(
    db: AsyncSession,
    intent_id: str,
    gateway_payment_intent_id: str | None = None,
    error_message: str | None = None,
) -> PaymentIntentTable | None:
    intent = await db.get(PaymentIntentTable, intent_id)
    if not intent:
        logger.warning("PaymentIntent %s not found for confirmation", intent_id)
        return None
    if error_message:
        intent.status = "failed"
        intent.error_message = error_message
        intent.updated_at = datetime.now(UTC)
        await db.flush()
        await db.refresh(intent)
        await _broadcast_payment_event(intent, "payment_failed")
        return intent
    intent.status = "succeeded"
    intent.gateway_payment_intent_id = gateway_payment_intent_id or intent.gateway_payment_intent_id
    intent.updated_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(intent)
    user = await db.get(UserTable, intent.user_id)
    if user:
        tier = _resolve_tier(intent.amount, intent.currency)
        await _apply_tier_upgrade(user, tier)
        await db.flush()
        await db.refresh(user)
        await _broadcast_payment_event(intent, "payment_succeeded", user=user)
    return intent


async def fail_pending_payment_intents_by_gateway(
    db: AsyncSession,
    gateway_payment_intent_id: str,
    error_message: str,
) -> list[PaymentIntentTable]:
    stmt = (
        select(PaymentIntentTable)
        .where(PaymentIntentTable.gateway_payment_intent_id == gateway_payment_intent_id)
        .where(PaymentIntentTable.status.in_(["initiated", "requires_confirmation"]))
    )
    intents = (await db.execute(stmt)).scalars().all()
    for intent in intents:
        intent.status = "failed"
        intent.error_message = error_message
        intent.updated_at = datetime.now(UTC)
        await _broadcast_payment_event(intent, "payment_failed")
    await db.flush()
    return list(intents)


def _resolve_tier(amount: float, currency: str) -> str:
    if currency.upper() == "INR":
        if amount >= 149900:
            return "elite"
        if amount >= 49900:
            return "pro"
        return "free"
    if amount >= 4900:
        return "elite"
    if amount >= 1900:
        return "pro"
    return "free"


async def _broadcast_payment_event(
    intent: PaymentIntentTable,
    event_type: str,
    user: UserTable | None = None,
) -> None:
    payload: dict[str, Any] = {
        "type": event_type,
        "payload": {
            "payment_intent_id": intent.id,
            "gateway": intent.gateway,
            "amount": intent.amount,
            "currency": intent.currency,
            "status": intent.status,
            "booking_id": intent.booking_id,
            "user_id": intent.user_id,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }
    if user:
        payload["payload"]["tier"] = user.tier
        payload["payload"]["subscription_status"] = user.subscription_status
    try:
        await publish_message(f"payment_update_{intent.user_id}", payload)
    except Exception as exc:
        logger.debug("Payment broadcast skipped for %s: %s", intent.user_id, exc)
    if user:
        try:
            quota = build_quota_snapshot(user)
            quota["source"] = event_type
            await publish_message(f"account_update_{intent.user_id}", {"type": "quota_update", "payload": quota})
        except Exception as exc:
            logger.debug("Quota broadcast skipped for %s: %s", intent.user_id, exc)
