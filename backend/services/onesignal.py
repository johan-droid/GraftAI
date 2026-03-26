import os
import httpx
from typing import Dict

ONE_SIGNAL_API_URL = "https://onesignal.com/api/v1/notifications"


def send_push_notification(user_player_ids: list[str], heading: str, content: str, data: Dict[str, str] = None):
    """Send push notification through OneSignal."""
    app_id = os.getenv("ONESIGNAL_APP_ID")
    api_key = os.getenv("ONESIGNAL_API_KEY")

    if not app_id or not api_key:
        raise RuntimeError("OneSignal integration requires ONESIGNAL_APP_ID and ONESIGNAL_API_KEY")

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

    resp = httpx.post(ONE_SIGNAL_API_URL, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()
