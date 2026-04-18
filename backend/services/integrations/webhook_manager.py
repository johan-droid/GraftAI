import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# STRIPPED DOWN: Muted for monolithic stability
# Webhook-based push notifications (Real-time Sync) are deprecated in favor
# of robust client-side polling and simple background sync workers.


async def register_user_webhooks(db: AsyncSession, user_id: str):
    logger.debug(
        f"Webhook registration skipped for {user_id}: Real-time push disabled."
    )
    return


async def renew_all_expiring_subscriptions(db: AsyncSession):
    return
