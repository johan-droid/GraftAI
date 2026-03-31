import os
import logging
import httpx
from typing import Optional
from msal import ConfidentialClientApplication

# Initialize logger
logger = logging.getLogger(__name__)

MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
# Common tenant for multi-tenant apps
MICROSOFT_AUTHORITY = "https://login.microsoftonline.com/common"

def get_ms_graph_token(token_data: dict) -> str:
    """Refreshes and returns a Microsoft Graph access token."""
    app = ConfidentialClientApplication(
        MICROSOFT_CLIENT_ID,
        authority=MICROSOFT_AUTHORITY,
        client_credential=MICROSOFT_CLIENT_SECRET,
    )
    
    # Try to get from refresh token
    result = app.acquire_token_by_refresh_token(
        token_data.get("refresh_token"), 
        scopes=token_data.get("scopes", "").split(",")
    )
    
    if "access_token" in result:
        return result["access_token"]
    
    logger.error(f"❌ MS Graph token refresh failed: {result.get('error_description')}")
    raise RuntimeError(f"Microsoft token refresh failed: {result.get('error')}")

async def create_teams_meeting(token_data: dict, event_details: dict) -> str:
    """
    Creates a Microsoft Teams online meeting via Graph API.
    Returns the join URL.
    """
    try:
        access_token = get_ms_graph_token(token_data)
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Structure for Microsoft Teams Online Meeting
        meeting_payload = {
            "subject": event_details.get("title", "GraftAI Teams Meeting"),
            "startDateTime": event_details["start_time"].isoformat(),
            "endDateTime": event_details["end_time"].isoformat(),
            "isEntryExitAnnounced": True,
            "allowedPresenters": "everyone",
            # Ensure the meeting is online
            "lobbyBypassSettings": {
                "scope": "everyone"
            }
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # First, we must use /me/onlineMeetings for personal accounts/Teams
            resp = await client.post(
                "https://graph.microsoft.com/v1.0/me/onlineMeetings",
                headers=headers,
                json=meeting_payload
            )
            
            if resp.status_code != 201:
                logger.error(f"❌ MS Graph API Error: {resp.status_code} - {resp.text}")
                raise RuntimeError(f"MS Graph API returned status {resp.status_code}")
            
            meeting_data = resp.json()
            join_url = meeting_data.get("joinWebUrl")
            
            logger.info(f"✅ Teams meeting created: {join_url}")
            return join_url

    except Exception as e:
        logger.error(f"❌ Unexpected error in Teams meeting creation: {e}")
        raise e

async def list_ms_events(access_token: str, delta_link: Optional[str] = None) -> dict:
    """
    Lists events from Microsoft Graph Calendar.
    Supports incremental sync via delta_link.
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Prefer": 'outlook.timezone="UTC"'
        }
        
        # If we have a delta_link, use it directly. Otherwise, initiate a new delta query.
        url = delta_link
        if not url:
            # For the initial delta query, we must provide start and end times.
            # Defaulting to 30 days back and 90 days forward.
            from datetime import timedelta, timezone
            start = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            end = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
            url = f"https://graph.microsoft.com/v1.0/me/calendar/calendarView/delta?startDateTime={start}&endDateTime={end}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            
            if resp.status_code == 410:
                # Delta token expired, restart sync
                logger.warning("🔄 Microsoft Delta link expired (410), restarting sync.")
                from datetime import timedelta, timezone
                start = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
                end = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
                url = f"https://graph.microsoft.com/v1.0/me/calendar/calendarView/delta?startDateTime={start}&endDateTime={end}"
                resp = await client.get(url, headers=headers)

            if resp.status_code != 200:
                logger.error(f"❌ MS Graph list_events error: {resp.status_code} - {resp.text}")
                raise RuntimeError(f"MS Graph list_events failed: {resp.status_code}")
                
            return resp.json()
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in MS Graph list_events: {e}")
        raise e

async def update_ms_event(token_data: dict, external_id: str, event_details: dict) -> dict:
    """Updates an existing Microsoft Graph calendar event."""
    try:
        access_token = get_ms_graph_token(token_data)
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Prefer": 'outlook.timezone="UTC"'
        }
        
        payload = {
            "subject": event_details.get("title"),
            "body": {
                "contentType": "HTML",
                "content": event_details.get("description")
            },
            "start": {
                "dateTime": event_details["start_time"].isoformat(),
                "timeZone": "UTC"
            } if "start_time" in event_details else None,
            "end": {
                "dateTime": event_details["end_time"].isoformat(),
                "timeZone": "UTC"
            } if "end_time" in event_details else None,
        }
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.patch(
                f"https://graph.microsoft.com/v1.0/me/events/{external_id}",
                headers=headers,
                json=payload
            )
            
            if resp.status_code != 200:
                logger.error(f"❌ MS Graph Update Error: {resp.status_code} - {resp.text}")
                raise RuntimeError(f"MS Graph API returned status {resp.status_code}")
                
            logger.info(f"✅ Microsoft Event updated: {external_id}")
            return resp.json()
    except Exception as e:
        logger.error(f"❌ MS Graph update failed for {external_id}: {e}")
        raise e

async def delete_ms_event(token_data: dict, external_id: str) -> None:
    """Deletes a Microsoft Graph calendar event."""
    try:
        access_token = get_ms_graph_token(token_data)
        
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(
                f"https://graph.microsoft.com/v1.0/me/events/{external_id}",
                headers=headers
            )
            
            if resp.status_code != 204:
                logger.error(f"❌ MS Graph Delete Error: {resp.status_code} - {resp.text}")
                raise RuntimeError(f"MS Graph API returned status {resp.status_code}")
                
            logger.info(f"✅ Microsoft Event deleted: {external_id}")
    except Exception as e:
        logger.error(f"❌ MS Graph delete failed for {external_id}: {e}")
        raise e
