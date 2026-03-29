import httpx
import logging
import uuid
from typing import Optional, Dict

logger = logging.getLogger(__name__)

MICROSOFT_GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/events"

async def create_microsoft_teams_link(
    title: str,
    start_time: str,
    end_time: str,
    access_token: Optional[str] = None
) -> Optional[str]:
    """
    Creates a Microsoft Outlook event with a Microsoft Teams link.
    Uses the user's OAuth access token.
    """
    if not access_token:
        logger.warning("No Microsoft access token provided. Falling back to simulation.")
        return None

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Request body according to Microsoft Graph API v1.0
    payload = {
        "subject": title,
        "start": {
            "dateTime": start_time,
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "UTC"
        },
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                MICROSOFT_GRAPH_API_URL,
                json=payload,
                headers=headers
            )
            
            if response.status_code != 201:
                logger.error(f"Microsoft Graph API error: {response.status_code} - {response.text}")
                return None

            data = response.json()
            online_meeting = data.get("onlineMeeting")
            if online_meeting:
                join_url = online_meeting.get("joinUrl")
                if join_url:
                    logger.info(f"Successfully created Microsoft Teams link: {join_url}")
                    return join_url
            
            logger.warning("Microsoft Outlook event created, but no Teams joinUrl returned.")
            return None

    except Exception as e:
        logger.error(f"Failed to call Microsoft Graph API: {e}")
        return None

async def get_microsoft_availability(
    start_time: str,
    end_time: str,
    access_token: str
) -> bool:
    """
    Checks if there are any conflicting events on the primary Microsoft Calendar.
    Returns True if the slot is FREE, False if BUSY.
    """
    url = "https://graph.microsoft.com/v1.0/me/calendar/getSchedule"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    # Microsoft needs an array of schedules
    payload = {
        "schedules": ["me"],
        "startTime": {
            "dateTime": start_time,
            "timeZone": "UTC"
        },
        "endTime": {
            "dateTime": end_time,
            "timeZone": "UTC"
        },
        "availabilityViewInterval": 60
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                logger.error(f"Microsoft getSchedule error: {response.status_code} - {response.text}")
                return True # Fail open

            data = response.json()
            # If any item in the value list has status other than 'free', consider it busy
            schedule_items = data.get("value", [{}])[0].get("scheduleItems", [])
            return len(schedule_items) == 0
    except Exception as e:
        logger.error(f"Failed to check Microsoft availability: {e}")
        return True # Fail open
