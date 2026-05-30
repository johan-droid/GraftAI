"""
Webhook delivery tasks with retry logic.
"""
import asyncio
import hashlib
import hmac
import json

import httpx

from backend.core.celery_app import celery_app
from backend.utils.logger import get_logger

logger = get_logger(__name__)

async def _send_webhook_request(subscriber_url: str, payload_json: str, headers: dict):
    """Async function to send webhook request."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        return await client.post(subscriber_url, content=payload_json, headers=headers)

@celery_app.task(bind=True, max_retries=10)
def deliver_webhook(self, webhook_id: str, subscriber_url: str, payload: dict, secret: str | None=None):
    """Deliver webhook to subscriber URL."""
    try:
        logger.info("Delivering webhook %s to %s", webhook_id, subscriber_url)
        payload_json = json.dumps(payload, default=str)
        headers = {"Content-Type": "application/json", "X-GraftAI-Event": payload.get("event", "unknown"), "X-GraftAI-Delivery": self.request.id}
        if secret:
            signature = hmac.new(secret.encode(), payload_json.encode(), hashlib.sha256).hexdigest()
            headers["X-GraftAI-Signature"] = f"sha256={signature}"
        response = asyncio.run(_send_webhook_request(subscriber_url, payload_json, headers))
        if response.status_code >= 200 and response.status_code < 300:
            logger.info("Webhook %s delivered successfully", webhook_id)
            log_webhook_delivery(webhook_id, True, response.status_code, None)
            return {"success": True, "status_code": response.status_code, "webhook_id": webhook_id}
        msg = f"HTTP {response.status_code}: {response.text}"
        raise Exception(msg)
    except Exception as exc:
        logger.exception("Webhook delivery failed: %s", exc)
        log_webhook_delivery(webhook_id, False, None, str(exc))
        countdown = min(60 * 2 ** self.request.retries, 86400)
        raise self.retry(exc=exc, countdown=countdown)

@celery_app.task(bind=True, max_retries=3)
def retry_failed_webhooks(self):
    """Retry failed webhook deliveries."""
    try:
        logger.info("Checking for failed webhooks to retry")
        return {"success": True, "retried": 0}
    except Exception as exc:
        logger.exception("Failed to retry webhooks: %s", exc)
        raise self.retry(exc=exc, countdown=300)

def log_webhook_delivery(webhook_id: str, success: bool, status_code: int | None=None, error: str | None=None):
    """Log webhook delivery attempt."""
    logger.info("Webhook delivery logged: %s, success=%s, status=%s, error=%s", webhook_id, success, status_code, error)
