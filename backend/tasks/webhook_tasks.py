"""
Webhook delivery tasks with retry logic.
"""

import json
import hmac
import hashlib
import asyncio
import httpx
from backend.core.celery_app import celery_app
from backend.utils.logger import get_logger

logger = get_logger(__name__)


async def _send_webhook_request(subscriber_url: str, payload_json: str, headers: dict):
    """Async function to send webhook request."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            subscriber_url, content=payload_json, headers=headers
        )
        return response


@celery_app.task(bind=True, max_retries=10)
def deliver_webhook(
    self, webhook_id: str, subscriber_url: str, payload: dict, secret: str = None
):
    """Deliver webhook to subscriber URL."""
    try:
        logger.info(f"Delivering webhook {webhook_id} to {subscriber_url}")

        # Prepare payload
        payload_json = json.dumps(payload, default=str)

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-GraftAI-Event": payload.get("event", "unknown"),
            "X-GraftAI-Delivery": self.request.id,
        }

        # Add HMAC signature if secret exists
        if secret:
            signature = hmac.new(
                secret.encode(), payload_json.encode(), hashlib.sha256
            ).hexdigest()
            headers["X-GraftAI-Signature"] = f"sha256={signature}"

        # Send request using asyncio
        response = asyncio.run(
            _send_webhook_request(subscriber_url, payload_json, headers)
        )

        # Check response
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"Webhook {webhook_id} delivered successfully")

            # Log successful delivery
            log_webhook_delivery(webhook_id, True, response.status_code, None)

            return {
                "success": True,
                "status_code": response.status_code,
                "webhook_id": webhook_id,
            }
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

    except Exception as exc:
        logger.error(f"Webhook delivery failed: {exc}")

        # Log failed attempt
        log_webhook_delivery(webhook_id, False, None, str(exc))

        # Retry with exponential backoff
        countdown = min(60 * (2**self.request.retries), 86400)  # Max 24 hours
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True, max_retries=3)
def retry_failed_webhooks(self):
    """Retry failed webhook deliveries."""
    try:
        logger.info("Checking for failed webhooks to retry")

        # Query failed deliveries that haven't exceeded max retries
        # This is a placeholder - actual implementation would query DB
        return {"success": True, "retried": 0}

    except Exception as exc:
        logger.error(f"Failed to retry webhooks: {exc}")
        raise self.retry(exc=exc, countdown=300)


def log_webhook_delivery(
    webhook_id: str, success: bool, status_code: int = None, error: str = None
):
    """Log webhook delivery attempt."""

    # In real implementation, insert into webhook_delivery_logs table
    logger.info(
        f"Webhook delivery logged: {webhook_id}, "
        f"success={success}, status={status_code}, error={error}"
    )
