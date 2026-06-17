import asyncio
import logging
import os
from datetime import UTC, datetime

from msal import ConfidentialClientApplication
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.integrations.token_service import ensure_valid_token
from backend.utils.http_client import ClientProxy, get_client

logger = logging.getLogger(__name__)
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_AUTHORITY = "https://login.microsoftonline.com/common"

async def get_ms_graph_client(db: AsyncSession, user_id: str) -> ClientProxy | None:
    """Returns an authenticated Microsoft Graph client for the given user with JIT rotation."""
    access_token = await ensure_valid_token(db, user_id, "microsoft")
    if not access_token:
        return None
    return ClientProxy(base_url="https://graph.microsoft.com/v1.0", headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"})

async def get_ms_graph_token(token_data: dict) -> str:
    """Refreshes and returns a Microsoft Graph access token."""
    app = await asyncio.to_thread(lambda: ConfidentialClientApplication(MICROSOFT_CLIENT_ID, authority=MICROSOFT_AUTHORITY, client_credential=MICROSOFT_CLIENT_SECRET))
    scopes = token_data.get("scopes") or ""
    if isinstance(scopes, str):
        scopes = [scope.strip() for scope in scopes.split(",") if scope.strip()]
    result = await asyncio.to_thread(app.acquire_token_by_refresh_token, token_data.get("refresh_token"), scopes=scopes)
    if "access_token" in result:
        return result["access_token"]
    logger.error(" MS Graph token refresh failed: %s", result.get("error_description"))
    msg = f"Microsoft token refresh failed: {result.get('error')}"
    raise RuntimeError(msg)

async def create_teams_meeting(token_data: dict, event_details: dict) -> str:
    """
    Creates a Microsoft Teams online meeting via Graph API.
    Returns the join URL.
    """
    try:
        access_token = await get_ms_graph_token(token_data)
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        meeting_payload = {"subject": event_details.get("title", "GraftAI Teams Meeting"), "startDateTime": event_details["start_time"].isoformat(), "endDateTime": event_details["end_time"].isoformat(), "isEntryExitAnnounced": True, "allowedPresenters": "everyone", "lobbyBypassSettings": {"scope": "everyone"}}
        client = await get_client()
        proxy = ClientProxy(client=client, base_url="https://graph.microsoft.com/v1.0", headers=headers)
        resp = await proxy.post("/me/onlineMeetings", json=meeting_payload)
        if resp.status_code != 201:
            logger.error(" MS Graph API Error: %s - %s", resp.status_code, resp.text)
            msg = f"MS Graph API returned status {resp.status_code}"
            raise RuntimeError(msg)
        meeting_data = resp.json()
        join_url = meeting_data.get("joinWebUrl")
        logger.info(" Teams meeting created: %s", join_url)
        return join_url
    except Exception as e:
        logger.exception(" Unexpected error in Teams meeting creation: %s", e)
        raise

async def list_ms_events(access_token: str, delta_link: str | None=None) -> dict:
    """
    Lists events from Microsoft Graph Calendar.
    Supports incremental sync via delta_link.
    """
    try:
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json", "Prefer": 'outlook.timezone="UTC"'}
        url = delta_link
        if not url:
            from datetime import timedelta
            start = (datetime.now(UTC) - timedelta(days=30)).isoformat()
            end = (datetime.now(UTC) + timedelta(days=90)).isoformat()
            url = f"/me/calendar/calendarView/delta?startDateTime={start}&endDateTime={end}"
        client = await get_client()
        proxy = ClientProxy(client=client, base_url="https://graph.microsoft.com/v1.0", headers=headers)
        items = []
        delta_link_result = None
        while url:
            resp = await proxy.get(url)
            if resp.status_code == 410:
                logger.warning(" Microsoft Delta link expired (410), restarting full-sync delta sequence.")
                from datetime import timedelta
                start = (datetime.now(UTC) - timedelta(days=30)).isoformat()
                end = (datetime.now(UTC) + timedelta(days=90)).isoformat()
                url = f"/me/calendar/calendarView/delta?startDateTime={start}&endDateTime={end}"
                items = []
                delta_link_result = None
                continue
            if resp.status_code != 200:
                logger.error(" MS Graph list_events error: %s - %s", resp.status_code, resp.text)
                msg = f"MS Graph list_events failed: {resp.status_code}"
                raise RuntimeError(msg)
            data = resp.json()
            items.extend(data.get("value", []))
            delta_link_result = data.get("@odata.deltaLink") or delta_link_result
            url = data.get("@odata.nextLink")
        return {"value": items, "@odata.deltaLink": delta_link_result}
    except Exception as e:
        logger.exception(" Unexpected error in MS Graph list_events: %s", e)
        raise

async def get_ms_user_principal_name(access_token: str) -> str | None:
    try:
        client = await get_client()
        proxy = ClientProxy(client=client, base_url="https://graph.microsoft.com/v1.0", headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"})
        resp = await proxy.get("/me")
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("mail") or data.get("userPrincipalName")
    except Exception as e:
        logger.warning("Failed to fetch Microsoft user principal name: %s", e)
        return None

async def get_ms_busy_times(access_token: str, user_principal_name: str, start_time: datetime, end_time: datetime) -> list[dict]:
    try:
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json", "Prefer": 'outlook.timezone="UTC"'}
        client = await get_client()
        proxy = ClientProxy(client=client, base_url="https://graph.microsoft.com/v1.0", headers=headers)
        payload = {"schedules": [user_principal_name], "startTime": {"dateTime": start_time.isoformat(), "timeZone": "UTC"}, "endTime": {"dateTime": end_time.isoformat(), "timeZone": "UTC"}, "availabilityViewInterval": 30}
        resp = await proxy.post("/me/calendar/getSchedule", json=payload)
        if resp.status_code != 200:
            logger.error(" MS Graph busy-time fetch failed: %s - %s", resp.status_code, resp.text)
            msg = f"MS Graph busy-time fetch failed: {resp.status_code}"
            raise RuntimeError(msg)
        data = resp.json()
        busy_times = []
        for item in data.get("value", []):
            for slot in item.get("scheduleItems", []):
                if slot.get("status") not in {"free", "unknown"}:
                    busy_times.append({"start": slot.get("start", {}).get("dateTime"), "end": slot.get("end", {}).get("dateTime"), "provider": "microsoft"})
        return busy_times
    except Exception as e:
        logger.exception(" Microsoft busy-time fetch failed: %s", e)
        raise

async def create_ms_event(token_data: dict, event_details: dict) -> dict:
    """
    Creates a Microsoft Graph calendar event with optional Teams link.
    """
    try:
        access_token = await get_ms_graph_token(token_data)
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json", "Prefer": 'outlook.timezone="UTC"'}
        is_meeting = event_details.get("is_meeting", False)
        payload = {"subject": event_details.get("title", "GraftAI Event"), "body": {"contentType": "HTML", "content": event_details.get("description", "")}, "start": {"dateTime": event_details["start_time"].isoformat(), "timeZone": "UTC"}, "end": {"dateTime": event_details["end_time"].isoformat(), "timeZone": "UTC"}, "isOnlineMeeting": is_meeting, "onlineMeetingProvider": "teamsForBusiness" if is_meeting else "unknown"}
        client = await get_client()
        proxy = ClientProxy(client=client, base_url="https://graph.microsoft.com/v1.0", headers=headers)
        resp = await proxy.post("/me/events", json=payload)
        if resp.status_code != 201:
            logger.error(" MS Graph create_event failed: %s - %s", resp.status_code, resp.text)
            msg = f"MS Graph create_event returned {resp.status_code}"
            raise RuntimeError(msg)
        return resp.json()
    except Exception as e:
        logger.exception(" Unexpected error in Microsoft event creation: %s", e)
        raise

async def update_ms_event(token_data: dict, external_id: str, event_details: dict) -> dict:
    """Updates an existing Microsoft Graph calendar event."""
    try:
        access_token = await get_ms_graph_token(token_data)
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json", "Prefer": 'outlook.timezone="UTC"'}
        payload = {"subject": event_details.get("title"), "body": {"contentType": "HTML", "content": event_details.get("description")}, "start": {"dateTime": event_details["start_time"].isoformat(), "timeZone": "UTC"} if "start_time" in event_details else None, "end": {"dateTime": event_details["end_time"].isoformat(), "timeZone": "UTC"} if "end_time" in event_details else None}
        payload = {k: v for k, v in payload.items() if v is not None}
        client = await get_client()
        proxy = ClientProxy(client=client, base_url="https://graph.microsoft.com/v1.0", headers=headers)
        resp = await proxy.patch(f"/me/events/{external_id}", json=payload)
        if resp.status_code != 200:
            logger.error(" MS Graph Update Error: %s - %s", resp.status_code, resp.text)
            msg = f"MS Graph API returned status {resp.status_code}"
            raise RuntimeError(msg)
        logger.info(" Microsoft Event updated: %s", external_id)
        return resp.json()
    except Exception as e:
        logger.exception(" MS Graph update failed for %s: %s", external_id, e)
        raise

async def delete_ms_event(token_data: dict, external_id: str) -> None:
    """Deletes a Microsoft Graph calendar event."""
    try:
        access_token = await get_ms_graph_token(token_data)
        headers = {"Authorization": f"Bearer {access_token}"}
        client = await get_client()
        proxy = ClientProxy(client=client, base_url="https://graph.microsoft.com/v1.0", headers=headers)
        resp = await proxy.delete(f"/me/events/{external_id}")
        if resp.status_code != 204:
            logger.error(" MS Graph Delete Error: %s - %s", resp.status_code, resp.text)
            msg = f"MS Graph API returned status {resp.status_code}"
            raise RuntimeError(msg)
        logger.info(" Microsoft Event deleted: %s", external_id)
    except Exception as e:
        logger.exception(" MS Graph delete failed for %s: %s", external_id, e)
        raise
