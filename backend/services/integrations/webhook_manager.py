import os
import uuid
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.tables import WebhookSubscriptionTable
from backend.models.user_token import UserTokenTable
from backend.services.integrations.google_calendar import get_google_service
from backend.services.integrations.ms_graph import get_ms_graph_client
from backend.utils.cache import acquire_lock, release_lock

logger = logging.getLogger(__name__)

async def register_user_webhooks(db: AsyncSession, user_id: str):
    """
    Subscribes to Google and Microsoft push notifications for a user based on connected accounts.
    """
    lock_name = f"webhook_register:{user_id}"
    if not await acquire_lock(lock_name, ttl_seconds=60):
        logger.info(f"⏳ Webhook registration already in progress for user {user_id}. Skipping.")
        return

    try:
    # 1. Google Subscriptions
        stmt = select(UserTokenTable).where(
            (UserTokenTable.user_id == user_id) & (UserTokenTable.provider == "google") & (UserTokenTable.is_active == True)
        )
        result = await db.execute(stmt)
        google_token = result.scalars().first()
        
        if google_token and not await _has_fresh_subscription(db, user_id, "google"):
            await _subscribe_google(db, user_id, google_token)
        elif google_token:
            logger.info(f"✅ Reusing existing Google webhook for user {user_id}")

    # 2. Microsoft Subscriptions
        stmt = select(UserTokenTable).where(
            (UserTokenTable.user_id == user_id) & (UserTokenTable.provider == "microsoft") & (UserTokenTable.is_active == True)
        )
        result = await db.execute(stmt)
        ms_token = result.scalars().first()
        
        if ms_token and not await _has_fresh_subscription(db, user_id, "microsoft"):
            await _subscribe_microsoft(db, user_id, ms_token)
        elif ms_token:
            logger.info(f"✅ Reusing existing Microsoft webhook for user {user_id}")
    finally:
        await release_lock(lock_name)


async def _has_fresh_subscription(
    db: AsyncSession,
    user_id: str,
    provider: str,
    min_valid_hours: int = 6,
) -> bool:
    threshold = datetime.now(timezone.utc) + timedelta(hours=min_valid_hours)
    stmt = select(WebhookSubscriptionTable).where(
        (WebhookSubscriptionTable.user_id == user_id)
        & (WebhookSubscriptionTable.provider == provider)
        & (WebhookSubscriptionTable.is_active == True)
        & (WebhookSubscriptionTable.expiration_at >= threshold)
    )
    result = await db.execute(stmt)
    return result.scalars().first() is not None

async def _subscribe_google(db: AsyncSession, user_id: str, token: UserTokenTable):
    """Watches the primary Google calendar."""
    try:
        service = await get_google_service(db, user_id)
        if not service:
            return

        channel_id = str(uuid.uuid4())
        webhook_url = f"{os.getenv('APP_BASE_URL')}/api/v1/webhooks/google"
        
        # Google 'watch' request
        body = {
            "id": channel_id,
            "type": "web_hook",
            "address": webhook_url,
            "params": {"ttl": "2592000"} # 30 days
        }
        
        watch_result = service.events().watch(calendarId="primary", body=body).execute()
        
        # Store metadata for renewal
        expiration_ms = int(watch_result.get("expiration"))
        expiration_at = datetime.fromtimestamp(expiration_ms / 1000.0, tz=timezone.utc)
        
        new_sub = WebhookSubscriptionTable(
            user_id=user_id,
            provider="google",
            external_subscription_id=channel_id,
            resource_id=watch_result.get("resourceId"),
            expiration_at=expiration_at
        )
        db.add(new_sub)
        await db.commit()
        logger.info(f"✅ Google Webhook registered for user {user_id} (ID: {channel_id})")
        
    except Exception as e:
        logger.error(f"❌ Google Webhook registration failed for {user_id}: {e}")

async def _subscribe_microsoft(db: AsyncSession, user_id: str, token: UserTokenTable):
    """Subscribes to Microsoft Graph event changes."""
    client = None
    try:
        client = await get_ms_graph_client(db, user_id)
        if not client:
            return

        sub_id = str(uuid.uuid4())
        client_state = str(uuid.uuid4())
        webhook_url = f"{os.getenv('APP_BASE_URL')}/api/v1/webhooks/microsoft"
        
        # Max expiration for Microsoft events is 4230 minutes (~3 days)
        expiration_at = datetime.now(timezone.utc) + timedelta(minutes=4000)
        
        payload = {
            "changeType": "updated,deleted",
            "notificationUrl": webhook_url,
            "resource": "me/events",
            "expirationDateTime": expiration_at.isoformat().replace("+00:00", "Z"),
            "clientState": client_state
        }
        
        response = await client.post("/subscriptions", json=payload)
        response.raise_for_status()
        sub_data = response.json()
        
        new_sub = WebhookSubscriptionTable(
            user_id=user_id,
            provider="microsoft",
            external_subscription_id=sub_data.get("id"),
            client_state=client_state,
            expiration_at=expiration_at
        )
        db.add(new_sub)
        await db.commit()
        logger.info(f"✅ MS Graph Webhook registered for user {user_id} (ID: {sub_data.get('id')})")
        
    except Exception as e:
        logger.error(f"❌ MS Webhook registration failed for {user_id}: {e}")
    finally:
        if client is not None:
            await client.aclose()

async def renew_all_expiring_subscriptions(db: AsyncSession):
    """
    Finds subscriptions expiring in the next 24 hours and renews or re-registers them.
    Microsoft needs renewal (PATCH), Google often needs re-registration (watch).
    """
    renewal_window = datetime.now(timezone.utc) + timedelta(hours=24)
    stmt = select(WebhookSubscriptionTable).where(
        (WebhookSubscriptionTable.expiration_at <= renewal_window) & (WebhookSubscriptionTable.is_active == True)
    )
    result = await db.execute(stmt)
    expiring_subs = result.scalars().all()
    
    logger.info(f"🔄 Checking {len(expiring_subs)} expiring subscriptions for renewal...")
    
    for sub in expiring_subs:
        # Simplest approach: Delete old and re-register new
        await db.delete(sub)
        await db.commit()
        await register_user_webhooks(db, sub.user_id)
        logger.info(f"♻️ Renewed/Re-registered {sub.provider} webhook for user {sub.user_id}")
