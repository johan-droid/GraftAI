import os
import httpx
import logging
from typing import Dict, List, Optional
from backend.utils.resilience import get_breaker

logger = logging.getLogger(__name__)

ONE_SIGNAL_API_URL = "https://onesignal.com/api/v1/notifications"

# Resilience: OneSignal Circuit Breaker
onesignal_breaker = get_breaker("onesignal", threshold=5, recovery_timeout=60)

async def send_push_notification(user_player_ids: List[str], heading: str, content: str, data: Optional[Dict[str, str]] = None):
    """
    Send push notification through OneSignal (Asynchronously & Resiliently).
    """
    app_id = os.getenv("ONESIGNAL_APP_ID")
    api_key = os.getenv("ONESIGNAL_API_KEY")

    if not app_id or not api_key:
        logger.warning("⚠️ OneSignal integration skipped: ONESIGNAL_APP_ID or ONESIGNAL_API_KEY missing.")
        return None

    payload = {
        "app_id": app_id,
        "include_player_ids": user_player_ids,
        "headings": {"en": heading},
        "contents": {"en": content},
        "data": data or {},
    }

    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json",
    }

    async def _perform_request():
        async with httpx.AsyncClient() as client:
            resp = await client.post(ONE_SIGNAL_API_URL, json=payload, headers=headers, timeout=10.0)
            resp.raise_for_status()
            return resp.json()

    try:
        # Wrap the outbound call in a circuit breaker
        return await onesignal_breaker(_perform_request)
    except Exception as e:
        logger.error(f"❌ [ONESIGNAL] Push notification failed: {e}")
        # We don't re-raise here to keep the notification pipeline from crashing
        return None
