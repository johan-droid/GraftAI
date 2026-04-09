import os
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.integrations.token_service import ensure_valid_token
from backend.utils.http_client import get_client

logger = logging.getLogger(__name__)

# Zoom configuration for User-Managed OAuth
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")

async def create_zoom_meeting(db: AsyncSession, user_id: str, event_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a Zoom meeting for a specific user and returns metadata.
    Leverages ensure_valid_token for JIT rotation.
    """
    try:
        access_token = await ensure_valid_token(db, user_id, "zoom")
        if not access_token:
            raise ValueError("Zoom authentication failed - no valid token available.")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        start_time = event_details.get("start_time")
        start_time_str = start_time.isoformat() if hasattr(start_time, "isoformat") else str(start_time)

        duration = 30
        if "end_time" in event_details and "start_time" in event_details:
            try:
                diff = event_details["end_time"] - event_details["start_time"]
                duration = int(diff.total_seconds() / 60)
            except Exception:
                pass

        payload = {
            "topic": event_details.get("title", "GraftAI Zoom Meeting"),
            "type": 2,
            "start_time": start_time_str,
            "duration": max(duration, 1),
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": True,
                "mute_upon_entry": True,
                "auto_recording": "none",
                "waiting_room": False
            }
        }
        
        client = await get_client()
        resp = await client.post(
            "https://api.zoom.us/v2/users/me/meetings",
            headers=headers,
            json=payload
        )
        
        if resp.status_code != 201:
            logger.error(f"❌ Zoom API Error: {resp.status_code} - {resp.text}")
            raise RuntimeError(f"Zoom API returned {resp.status_code}")
                
        data = resp.json()
        return {
            "id": str(data.get("id")),
            "join_url": data.get("join_url")
        }
    except Exception as e:
        logger.error(f"❌ Zoom meeting creation fail: {e}")
        import uuid
        return {
            "id": None,
            "join_url": f"https://meet.graftai.tech/zoom-fallback-{uuid.uuid4().hex[:8]}"
        }


async def update_zoom_meeting(db: AsyncSession, user_id: str, meeting_id: str, event_details: Dict[str, Any]) -> None:
    """
    Updates an existing Zoom meeting.
    """
    try:
        access_token = await ensure_valid_token(db, user_id, "zoom")
        if not access_token:
            raise ValueError("Zoom authentication failed - no valid token available.")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        start_time = event_details.get("start_time")
        start_time_str = start_time.isoformat() if hasattr(start_time, "isoformat") else str(start_time)
        duration = 30
        if "end_time" in event_details and "start_time" in event_details:
            try:
                diff = event_details["end_time"] - event_details["start_time"]
                duration = int(diff.total_seconds() / 60)
            except Exception:
                pass

        payload = {
            "topic": event_details.get("title", "GraftAI Zoom Meeting"),
            "type": 2,
            "start_time": start_time_str,
            "duration": max(duration, 1),
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": True,
                "mute_upon_entry": True,
                "auto_recording": "none",
                "waiting_room": False
            }
        }

        client = await get_client()
        resp = await client.patch(
            f"https://api.zoom.us/v2/meetings/{meeting_id}",
            headers=headers,
            json=payload
        )

        if resp.status_code not in (200, 204):
            logger.error(f"❌ Zoom update failed: {resp.status_code} - {resp.text}")
            raise RuntimeError(f"Zoom update failed with status {resp.status_code}")
    except Exception as e:
        logger.error(f"❌ Zoom meeting update failed: {e}")
        raise


async def delete_zoom_meeting(db: AsyncSession, user_id: str, meeting_id: str) -> None:
    """
    Deletes a Zoom meeting by ID.
    """
    try:
        access_token = await ensure_valid_token(db, user_id, "zoom")
        if not access_token:
            raise ValueError("Zoom authentication failed - no valid token available.")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        client = await get_client()
        resp = await client.delete(
            f"https://api.zoom.us/v2/meetings/{meeting_id}",
            headers=headers
        )

        if resp.status_code not in (204, 202):
            logger.error(f"❌ Zoom delete failed: {resp.status_code} - {resp.text}")
            raise RuntimeError(f"Zoom delete failed with status {resp.status_code}")
    except Exception as e:
        logger.error(f"❌ Zoom meeting deletion failed: {e}")
        raise

async def list_zoom_meetings(db: AsyncSession, user_id: str) -> list:
    """
    Fetches a list of upcoming Zoom meetings for context ingestion using JIT tokens.
    """
    try:
        access_token = await ensure_valid_token(db, user_id, "zoom")
        if not access_token:
            return []

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        client = await get_client()
        resp = await client.get(
            "https://api.zoom.us/v2/users/me/meetings?type=upcoming&page_size=30",
            headers=headers
        )

        if resp.status_code != 200:
            return []

        return resp.json().get("meetings", [])

    except Exception as e:
        logger.error(f"❌ Error listing Zoom meetings: {e}")
        return []
