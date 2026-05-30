import logging

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def register_user_webhooks(db: AsyncSession, user_id: str):
    logger.debug("Webhook registration skipped for %s: Real-time push disabled.", user_id)

async def renew_all_expiring_subscriptions(db: AsyncSession):
    return
