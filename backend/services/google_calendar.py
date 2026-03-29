import httpx
import logging
import uuid
from typing import Optional, Dict

logger = logging.getLogger(__name__)

GOOGLE_CALENDAR_API_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

async def create_google_meet_link(
    title: str,
    start_time: str,
    end_time: str,
    access_token: Optional[str] = None
) -> Optional[str]:
    """
    Creates a Google Calendar event with a Google Meet link.
    Uses the user's OAuth access token.
    """
    if not access_token:
        logger.warning("No Google access token provided. Falling back to simulation.")
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Request body according to Google Calendar API v3
    payload = {
        "summary": title,
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutMeet"}
            }
        }
    }

    params = {
        "conferenceDataVersion": 1
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                GOOGLE_CALENDAR_API_URL,
                json=payload,
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                logger.error(f"Google Calendar API error: {response.status_code} - {response.text}")
                return None

            data = response.json()
            hangout_link = data.get("hangoutLink")
            
            if hangout_link:
                logger.info(f"Successfully created Google Meet link: {hangout_link}")
                return hangout_link
            else:
                logger.warning("Google Calendar event created, but no hangoutLink returned.")
                return None

    except Exception as e:
        logger.error(f"Failed to call Google Calendar API: {e}")
        return None

async def get_google_availability(
    start_time: str,
    end_time: str,
    access_token: str
) -> bool:
    """
    Checks if there are any conflicting events on the primary Google Calendar.
    Returns True if the slot is FREE, False if BUSY.
    """
    url = "https://www.googleapis.com/calendar/v3/freeBusy"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "timeMin": start_time,
        "timeMax": end_time,
        "items": [{"id": "primary"}]
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                logger.error(f"Google FreeBusy error: {response.status_code}")
                return True # Fail open

            data = response.json()
            busy_slots = data.get("calendars", {}).get("primary", {}).get("busy", [])
            return len(busy_slots) == 0
    except Exception as e:
        logger.error(f"Failed to check Google availability: {e}")
        return True # Fail open
