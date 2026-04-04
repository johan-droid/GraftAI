import logging
from fastapi import APIRouter, Request, Response, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.api.deps import get_db
from backend.models.tables import WebhookSubscriptionTable
from backend.utils.cache import invalidate_user_calendar_cache
from backend.utils.arq_utils import enqueue_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/google")
async def google_calendar_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handles Google Calendar push notifications.
    """
    resource_id = request.headers.get("X-Goog-Resource-ID")
    subscription_id = request.headers.get("X-Goog-Channel-ID")
    state = request.headers.get("X-Goog-Resource-State")

    logger.info(f"[WEBHOOK] 📩 Google Notification: SubID={subscription_id}, State={state}")

    if state == "sync":
        # Initial verification message, just return 200
        return Response(status_code=200)

    # Find the user associated with this subscription
    stmt = select(WebhookSubscriptionTable).where(
        WebhookSubscriptionTable.external_subscription_id == subscription_id
    )
    result = await db.execute(stmt)
    sub = result.scalars().first()

    if sub:
        # 1. Invalidate Cache
        invalidate_user_calendar_cache(sub.user_id)
        # 2. Enqueue background sync
        await enqueue_job("task_sync_calendar", user_id=sub.user_id)
        logger.info(f"[WEBHOOK] 🔄 Triggered background sync for user {sub.user_id}")

    return Response(status_code=200)

@router.post("/microsoft")
async def microsoft_graph_webhook(
    request: Request,
    validationToken: str = None,
    db: AsyncSession = Depends(get_db)
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
                invalidate_user_calendar_cache(sub.user_id)
                await enqueue_job("task_sync_calendar", user_id=sub.user_id)
        
    except Exception as e:
        logger.error(f"[WEBHOOK] ❌ Parse failure: {e}")

    return Response(status_code=202)
