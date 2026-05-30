import json
import logging
import os
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import UserTokenTable
from backend.services.integrations.token_service import ensure_valid_token
from backend.services.token_encryption import decrypt_token_value

logger = logging.getLogger(__name__)

def _resolve_google_calendar_credentials() -> tuple[str | None, str | None]:
    client_id = os.getenv("GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_ID") or os.getenv("NEXTAUTH_GOOGLE_ID") or os.getenv("AUTH_GOOGLE_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET") or os.getenv("GOOGLE_SECRET") or os.getenv("NEXTAUTH_GOOGLE_SECRET") or os.getenv("AUTH_GOOGLE_SECRET")
    return (client_id, client_secret)

async def get_google_service(db: AsyncSession, user_id: str):
    """Builds an authenticated Google Calendar service for the given user with JIT rotation."""
    access_token = await ensure_valid_token(db, user_id, "google")
    if not access_token:
        return None
    stmt = select(UserTokenTable).where((UserTokenTable.user_id == user_id) & (UserTokenTable.provider == "google"))
    res = await db.execute(stmt)
    token = res.scalars().first()
    refresh_token = None
    if token:
        refresh_token, _ = decrypt_token_value(token.refresh_token)
        if refresh_token is None:
            logger.error("Cannot build Google service. Token decryption failed for token ID %s", token.id)
            return None
    token_data = {"access_token": access_token, "refresh_token": refresh_token, "scopes": token.scopes if token else ""}
    creds = get_google_credentials(token_data)
    return build("calendar", "v3", credentials=creds)

def get_google_credentials(token_data: dict) -> Credentials:
    """Reconstructs Google credentials from stored token data."""
    client_id, client_secret = _resolve_google_calendar_credentials()
    if not client_id or not client_secret:
        logger.error("❌ CRITICAL: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is missing from environment. Also check GOOGLE_ID/GOOGLE_SECRET, NEXTAUTH_GOOGLE_ID/NEXTAUTH_GOOGLE_SECRET, or AUTH_GOOGLE_ID/AUTH_GOOGLE_SECRET.")
    scopes = token_data.get("scopes", [])
    if isinstance(scopes, str):
        try:
            scopes = json.loads(scopes)
        except json.JSONDecodeError:
            scopes = [scope.strip() for scope in scopes.replace(",", " ").split() if scope.strip()]
    creds = Credentials(token=token_data.get("access_token"), refresh_token=token_data.get("refresh_token"), token_uri="https://oauth2.googleapis.com/token", client_id=client_id, client_secret=client_secret, scopes=scopes)
    try:
        if creds and creds.expired and creds.refresh_token:
            if not client_id or not client_secret or (not creds.token_uri):
                logger.warning("⚠️ Skipping auto-refresh: missing client credentials or token_uri.")
            else:
                creds.refresh(Request())
    except Exception as e:
        logger.warning("⚠️ Failed to refresh Google credentials: %s", e)
    return creds

async def create_google_meet_event(token_data: dict, event_details: dict) -> str:
    """
    Creates a Google Calendar event with a Google Meet link.
    Returns the conference link (Meet URL).
    """
    try:
        creds = get_google_credentials(token_data)
        service = build("calendar", "v3", credentials=creds)
        event = {"summary": event_details.get("title", "GraftAI Meeting"), "description": event_details.get("description", ""), "start": {"dateTime": event_details["start_time"].isoformat(), "timeZone": "UTC"}, "end": {"dateTime": event_details["end_time"].isoformat(), "timeZone": "UTC"}, "conferenceData": {"createRequest": {"requestId": f"graftai-{datetime.now().timestamp()}", "conferenceSolutionKey": {"type": "hangoutsMeet"}}}, "attendees": [{"email": e} for e in event_details.get("attendees", [])]}
        created_event = service.events().insert(calendarId="primary", body=event, conferenceDataVersion=1).execute()
        meet_link = created_event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")
        if not meet_link:
            meet_link = created_event.get("htmlLink")
        logger.info("✅ Google Meet created: %s", meet_link)
        return meet_link
    except HttpError as error:
        logger.exception("❌ Google Calendar API failed: %s", error)
        msg = f"Could not create Google Meet: {error}"
        raise RuntimeError(msg)
    except Exception as e:
        logger.exception("❌ Unexpected error in Google Meet creation: %s", e)
        raise

async def create_google_event(token_data: dict, event_details: dict) -> dict:
    """
    Creates a standard Google Calendar event.
    Returns the created event object from Google.
    """
    try:
        creds = get_google_credentials(token_data)
        service = build("calendar", "v3", credentials=creds)
        event = {"summary": event_details.get("title", "GraftAI Event"), "description": event_details.get("description", ""), "start": {"dateTime": event_details["start_time"].isoformat(), "timeZone": event_details.get("timezone", "UTC")}, "end": {"dateTime": event_details["end_time"].isoformat(), "timeZone": event_details.get("timezone", "UTC")}, "attendees": [{"email": e} for e in event_details.get("attendees", [])]}
        if event_details.get("is_meeting"):
            event["conferenceData"] = {"createRequest": {"requestId": f"graftai-{datetime.now().timestamp()}", "conferenceSolutionKey": {"type": "hangoutsMeet"}}}
        insert_args = {"calendarId": "primary", "body": event}
        if event_details.get("is_meeting"):
            insert_args["conferenceDataVersion"] = 1
        created_event = service.events().insert(**insert_args).execute()
        logger.info("✅ Google Event created: %s", created_event.get("id"))
        return created_event
    except HttpError as error:
        logger.exception("❌ Google Calendar API failed: %s", error)
        msg = f"Could not create Google event: {error}"
        raise RuntimeError(msg)
    except Exception as e:
        logger.exception("❌ Unexpected error in Google event creation: %s", e)
        raise

async def list_google_events(token_data: dict, calendar_id: str="primary", sync_token: str | None=None) -> dict:
    """
    Lists events from Google Calendar.
    Supports incremental sync via sync_token and handles pagination transparently.
    """
    try:
        creds = get_google_credentials(token_data)
        service = build("calendar", "v3", credentials=creds)
        all_items = []
        next_sync_token = None
        page_token = None
        while True:
            params = {"calendarId": calendar_id, "singleEvents": not sync_token, "orderBy": "startTime" if not sync_token else None, "showDeleted": bool(sync_token)}
            if sync_token:
                params["syncToken"] = sync_token
            if page_token:
                params["pageToken"] = page_token
            response = service.events().list(**{k: v for k, v in params.items() if v is not None}).execute()
            all_items.extend(response.get("items", []) or [])
            next_sync_token = response.get("nextSyncToken") or next_sync_token
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return {"items": all_items, "nextSyncToken": next_sync_token}
    except HttpError as error:
        if error.resp.status == 410:
            logger.warning("🔄 Google Sync token expired (410), performing full sync for %s", calendar_id)
            service = build("calendar", "v3", credentials=get_google_credentials(token_data))
            response = service.events().list(calendarId=calendar_id, singleEvents=True, orderBy="startTime").execute()
            return {"items": response.get("items", []) or [], "nextSyncToken": response.get("nextSyncToken")}
        logger.exception("❌ Google list_events failed: %s", error)
        raise

async def get_google_busy_times(token_data: dict, start_time: datetime, end_time: datetime, calendar_id: str="primary") -> list[dict]:
    """Fetches busy windows from Google Calendar freebusy."""
    try:
        creds = get_google_credentials(token_data)
        service = build("calendar", "v3", credentials=creds)
        response = service.freebusy().query(requestBody={"timeMin": start_time.isoformat(), "timeMax": end_time.isoformat(), "items": [{"id": calendar_id}]}).execute()
        busy_entries = response.get("calendars", {}).get(calendar_id, {}).get("busy", [])
        return [{"start": busy.get("start"), "end": busy.get("end"), "provider": "google"} for busy in busy_entries]
    except HttpError as error:
        logger.exception("❌ Google busy-time fetch failed: %s", error)
        raise

async def update_google_event(token_data: dict, external_id: str, event_details: dict) -> dict:
    """Updates an existing Google Calendar event."""
    try:
        creds = get_google_credentials(token_data)
        service = build("calendar", "v3", credentials=creds)
        event = {"summary": event_details.get("title"), "description": event_details.get("description"), "start": {"dateTime": event_details["start_time"].isoformat(), "timeZone": "UTC"} if "start_time" in event_details else None, "end": {"dateTime": event_details["end_time"].isoformat(), "timeZone": "UTC"} if "end_time" in event_details else None}
        event = {k: v for k, v in event.items() if v is not None}
        updated_event = service.events().patch(calendarId="primary", eventId=external_id, body=event).execute()
        logger.info("✅ Google Event updated: %s", external_id)
        return updated_event
    except Exception as e:
        logger.exception("❌ Google update failed for %s: %s", external_id, e)
        raise

async def delete_google_event(token_data: dict, external_id: str) -> None:
    """Deletes a Google Calendar event."""
    try:
        creds = get_google_credentials(token_data)
        service = build("calendar", "v3", credentials=creds)
        service.events().delete(calendarId="primary", eventId=external_id).execute()
        logger.info("✅ Google Event deleted: %s", external_id)
    except Exception as e:
        logger.exception("❌ Google delete failed for %s: %s", external_id, e)
        raise
