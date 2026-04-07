import os
import logging
import httpx
from typing import Optional
from msal import ConfidentialClientApplication
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user_token import UserTokenTable
from backend.utils.http_client import get_client, ClientProxy

# Initialize logger
logger = logging.getLogger(__name__)

MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
# Common tenant for multi-tenant apps
MICROSOFT_AUTHORITY = "https://login.microsoftonline.com/common"


async def get_ms_graph_client(db: AsyncSession, user_id: str) -> Optional[ClientProxy]:
    """Returns an authenticated Microsoft Graph client for the given user."""
    stmt = select(UserTokenTable).where(
        (UserTokenTable.user_id == user_id)
        & (UserTokenTable.provider == "microsoft")
        & (UserTokenTable.is_active == True)
    )
    result = await db.execute(stmt)
    token = result.scalars().first()
    if not token:
        logger.info(f"No active Microsoft token found for user {user_id}")
        return None

    access_token = get_ms_graph_token(
        {
            "refresh_token": token.refresh_token,
            "scopes": token.scopes or "",
        }
    )

    client = await get_client()
    return ClientProxy(
        client=client,
        base_url="https://graph.microsoft.com/v1.0",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )

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
        
        client = await get_client()
        proxy = ClientProxy(
            client=client,
            base_url="https://graph.microsoft.com/v1.0",
            headers=headers
        )
        
        # First, we must use /me/onlineMeetings for personal accounts/Teams
        resp = await proxy.post(
            "/me/onlineMeetings",
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
            url = f"/me/calendar/calendarView/delta?startDateTime={start}&endDateTime={end}"

        client = await get_client()
        proxy = ClientProxy(
            client=client,
            base_url="https://graph.microsoft.com/v1.0",
            headers=headers
        )

        resp = await proxy.get(url)
        
        if resp.status_code == 410:
            # Delta token expired, restart sync
            logger.warning("🔄 Microsoft Delta link expired (410), restarting sync.")
            from datetime import timedelta, timezone
            start = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            end = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
            url = f"/me/calendar/calendarView/delta?startDateTime={start}&endDateTime={end}"
            resp = await proxy.get(url)

        if resp.status_code != 200:
            logger.error(f"❌ MS Graph list_events error: {resp.status_code} - {resp.text}")
            raise RuntimeError(f"MS Graph list_events failed: {resp.status_code}")
            
        return resp.json()
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in MS Graph list_events: {e}")
        raise e

async def create_ms_event(token_data: dict, event_details: dict) -> dict:
    """
    Creates a Microsoft Graph calendar event with optional Teams link.
    """
    try:
        access_token = get_ms_graph_token(token_data)
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Prefer": 'outlook.timezone="UTC"'
        }
        is_meeting = event_details.get("is_meeting", False)
        payload = {
            "subject": event_details.get("title", "GraftAI Event"),
            "body": {"contentType": "HTML", "content": event_details.get("description", "")},
            "start": {"dateTime": event_details["start_time"].isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": event_details["end_time"].isoformat(), "timeZone": "UTC"},
            "isOnlineMeeting": is_meeting,
            # We don't specify provider to let Microsoft default based on account type, 
            # or we could try 'teamsForBusiness' and fallback.
            # Actually, omitting it often works better for personal accounts.
            "onlineMeetingProvider": "teamsForBusiness" if is_meeting else "unknown"
        }
        
        client = await get_client()
        proxy = ClientProxy(
            client=client,
            base_url="https://graph.microsoft.com/v1.0",
            headers=headers
        )
        
        # Fallback for Personal accounts: if teamsForBusiness fails, we can retry without it or with teamsForLife
        resp = await proxy.post("/me/events", json=payload)
        if resp.status_code != 201:
            logger.error(f"❌ MS Graph create_event failed: {resp.status_code} - {resp.text}")
            raise RuntimeError(f"MS Graph create_event returned {resp.status_code}")
        return resp.json()
    except Exception as e:
        logger.error(f"❌ Unexpected error in Microsoft event creation: {e}")
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
        
        client = await get_client()
        proxy = ClientProxy(
            client=client,
            base_url="https://graph.microsoft.com/v1.0",
            headers=headers
        )
        
        resp = await proxy.patch(
            f"/me/events/{external_id}",
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
        
        client = await get_client()
        proxy = ClientProxy(
            client=client,
            base_url="https://graph.microsoft.com/v1.0",
            headers=headers
        )
        
        resp = await proxy.delete(f"/me/events/{external_id}")
        
        if resp.status_code != 204:
            logger.error(f"❌ MS Graph Delete Error: {resp.status_code} - {resp.text}")
            raise RuntimeError(f"MS Graph API returned status {resp.status_code}")
            
        logger.info(f"✅ Microsoft Event deleted: {external_id}")
    except Exception as e:
        logger.error(f"❌ MS Graph delete failed for {external_id}: {e}")
        raise e
