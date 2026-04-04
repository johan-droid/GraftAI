import logging
import os
from typing import Optional
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Initialize logger
logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

def get_google_credentials(token_data: dict) -> Credentials:
    """Reconstructs Google credentials from stored token data."""
    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=token_data.get("scopes", "").split(",")
    )
    
    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        
    return creds

async def create_google_meet_event(token_data: dict, event_details: dict) -> str:
    """
    Creates a Google Calendar event with a Google Meet link.
    Returns the conference link (Meet URL).
    """
    try:
        creds = get_google_credentials(token_data)
        service = build("calendar", "v3", credentials=creds)

        # Standard Google Meet event structure
        event = {
            "summary": event_details.get("title", "GraftAI Meeting"),
            "description": event_details.get("description", ""),
            "start": {
                "dateTime": event_details["start_time"].isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": event_details["end_time"].isoformat(),
                "timeZone": "UTC",
            },
            "conferenceData": {
                "createRequest": {
                    "requestId": f"graftai-{datetime.now().timestamp()}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
            "attendees": [{"email": e} for e in event_details.get("attendees", [])],
        }

        # Insert event with conferenceDataVersion=1 to trigger Meet link generation
        created_event = service.events().insert(
            calendarId="primary",
            body=event,
            conferenceDataVersion=1
        ).execute()

        # Extract conference link
        meet_link = created_event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")
        if not meet_link:
            # Fallback if meet link generation failed for some reason
            meet_link = created_event.get("htmlLink")
            
        logger.info(f"✅ Google Meet created: {meet_link}")
        return meet_link

    except HttpError as error:
        logger.error(f"❌ Google Calendar API failed: {error}")
        raise RuntimeError(f"Could not create Google Meet: {error}")
    except Exception as e:
        logger.error(f"❌ Unexpected error in Google Meet creation: {e}")
        raise e


async def create_google_event(token_data: dict, event_details: dict) -> dict:
    """
    Creates a standard Google Calendar event.
    Returns the created event object from Google.
    """
    try:
        creds = get_google_credentials(token_data)
        service = build("calendar", "v3", credentials=creds)

        event = {
            "summary": event_details.get("title", "GraftAI Event"),
            "description": event_details.get("description", ""),
            "start": {
                "dateTime": event_details["start_time"].isoformat(),
                "timeZone": event_details.get("timezone", "UTC"),
            },
            "end": {
                "dateTime": event_details["end_time"].isoformat(),
                "timeZone": event_details.get("timezone", "UTC"),
            },
            "attendees": [{"email": e} for e in event_details.get("attendees", [])],
        }

        created_event = service.events().insert(
            calendarId="primary",
            body=event
        ).execute()

        logger.info(f"✅ Google Event created: {created_event.get('id')}")
        return created_event

    except HttpError as error:
        logger.error(f"❌ Google Calendar API failed: {error}")
        raise RuntimeError(f"Could not create Google event: {error}")
    except Exception as e:
        logger.error(f"❌ Unexpected error in Google event creation: {e}")
        raise e

async def list_google_events(token_data: dict, calendar_id: str = "primary", sync_token: Optional[str] = None) -> dict:
    """
    Lists events from Google Calendar. 
    Supports incremental sync via sync_token.
    """
    try:
        creds = get_google_credentials(token_data)
        service = build("calendar", "v3", credentials=creds)

        request = service.events().list(
            calendarId=calendar_id,
            syncToken=sync_token,
            singleEvents=True,
            orderBy="startTime",
        )
        return request.execute()
    except HttpError as error:
        if error.resp.status == 410:
            logger.warning(f"🔄 Google Sync token expired (410), performing full sync for {calendar_id}")
            service = build("calendar", "v3", credentials=get_google_credentials(token_data))
            return service.events().list(calendarId=calendar_id, singleEvents=True, orderBy="startTime").execute()

        logger.error(f"❌ Google list_events failed: {error}")
        raise error

async def update_google_event(token_data: dict, external_id: str, event_details: dict) -> dict:
    """Updates an existing Google Calendar event."""
    try:
        creds = get_google_credentials(token_data)
        service = build("calendar", "v3", credentials=creds)
        
        # Partially update the event
        event = {
            "summary": event_details.get("title"),
            "description": event_details.get("description"),
            "start": {
                "dateTime": event_details["start_time"].isoformat(),
                "timeZone": "UTC",
            } if "start_time" in event_details else None,
            "end": {
                "dateTime": event_details["end_time"].isoformat(),
                "timeZone": "UTC",
            } if "end_time" in event_details else None,
        }
        # Remove None values
        event = {k: v for k, v in event.items() if v is not None}
        
        updated_event = service.events().patch(
            calendarId="primary",
            eventId=external_id,
            body=event
        ).execute()
        
        logger.info(f"✅ Google Event updated: {external_id}")
        return updated_event
    except Exception as e:
        logger.error(f"❌ Google update failed for {external_id}: {e}")
        raise e

async def delete_google_event(token_data: dict, external_id: str) -> None:
    """Deletes a Google Calendar event."""
    try:
        creds = get_google_credentials(token_data)
        service = build("calendar", "v3", credentials=creds)
        
        service.events().delete(
            calendarId="primary",
            eventId=external_id
        ).execute()
        
        logger.info(f"✅ Google Event deleted: {external_id}")
    except Exception as e:
        logger.error(f"❌ Google delete failed for {external_id}: {e}")
        raise e
