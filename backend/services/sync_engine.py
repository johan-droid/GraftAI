import os
import logging
import json
from datetime import datetime, timedelta, timezone
import httpx
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.tables import UserTable, EventTable
from backend.utils.security import decrypt_token
from backend.utils.db import get_db

logger = logging.getLogger(__name__)

class SyncEngine:
    """
    Sovereign Sync Engine for Hard Integration with External Calendars.
    Handles token refreshing, event fetching, and sovereign merging into local state.
    """
    
    def __init__(self):
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.microsoft_client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.microsoft_client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")

    async def _refresh_google_token(self, user: UserTable, db: AsyncSession) -> Optional[str]:
        refresh_token = decrypt_token(user.google_refresh_token)
        if not refresh_token: return None
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.google_client_id,
                    "client_secret": self.google_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                from backend.utils.security import encrypt_token
                user.google_access_token = encrypt_token(data["access_token"])
                user.google_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
                # Google might not return a new refresh token unless prompted
                if "refresh_token" in data:
                    user.google_refresh_token = encrypt_token(data["refresh_token"])
                await db.commit()
                return data["access_token"]
        return None

    async def _refresh_microsoft_token(self, user: UserTable, db: AsyncSession) -> Optional[str]:
        refresh_token = decrypt_token(user.microsoft_refresh_token)
        if not refresh_token: return None
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data={
                    "client_id": self.microsoft_client_id,
                    "client_secret": self.microsoft_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                    "scope": "openid profile email User.Read Calendars.Read",
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                from backend.utils.security import encrypt_token
                user.microsoft_access_token = encrypt_token(data["access_token"])
                user.microsoft_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
                if "refresh_token" in data:
                    user.microsoft_refresh_token = encrypt_token(data["refresh_token"])
                await db.commit()
                return data["access_token"]
        return None

    async def sync_google_calendar(self, user_id: str, db: AsyncSession):
        user = await db.get(UserTable, user_id)
        if not user or not user.google_access_token: return
        
        token = decrypt_token(user.google_access_token)
        # Auto-refresh if expired
        if user.google_token_expires_at and datetime.now(timezone.utc) > user.google_token_expires_at - timedelta(minutes=5):
            token = await self._refresh_google_token(user, db)
            
        if not token: return

        async with httpx.AsyncClient() as client:
            # Fetch events from now to 30 days ahead
            time_min = datetime.now(timezone.utc).isoformat()
            time_max = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            
            resp = await client.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers={"Authorization": f"Bearer {token}"},
                params={"timeMin": time_min, "timeMax": time_max, "singleEvents": True}
            )
            
            if resp.status_code != 200:
                logger.error(f"Google Sync Failed for {user_id}: HTTP {resp.status_code}")
                return

            events = resp.json().get("items", [])
            for item in events:
                await self._upsert_external_event(db, user_id, "google", item)

    async def sync_microsoft_calendar(self, user_id: str, db: AsyncSession):
        user = await db.get(UserTable, user_id)
        if not user or not user.microsoft_access_token: return
        
        token = decrypt_token(user.microsoft_access_token)
        if user.microsoft_token_expires_at and datetime.now(timezone.utc) > user.microsoft_token_expires_at - timedelta(minutes=5):
            token = await self._refresh_microsoft_token(user, db)
            
        if not token: return

        async with httpx.AsyncClient() as client:
            # MS Graph uses ISO8601 strings in query
            start_dt = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            end_dt = (datetime.now(timezone.utc) + timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            resp = await client.get(
                f"https://graph.microsoft.com/v1.0/me/calendarview",
                headers={"Authorization": f"Bearer {token}"},
                params={"startDateTime": start_dt, "endDateTime": end_dt}
            )
            
            if resp.status_code != 200:
                logger.error(f"MS Sync Failed for {user_id}: HTTP {resp.status_code}")
                return

            events = resp.json().get("value", [])
            for item in events:
                await self._upsert_external_event(db, user_id, "microsoft", item)

    async def _upsert_external_event(self, db: AsyncSession, user_id: str, source: str, raw_event: Dict[str, Any]):
        try:
            ext_id = raw_event.get("id")
            if not ext_id: return

            # Extract common fields
            title = ""
            start_str = ""
            end_str = ""
            
            if source == "google":
                title = raw_event.get("summary", "No Title")
                start_str = raw_event.get("start", {}).get("dateTime") or raw_event.get("start", {}).get("date")
                end_str = raw_event.get("end", {}).get("dateTime") or raw_event.get("end", {}).get("date")
            else: # microsoft
                title = raw_event.get("subject", "No Title")
                start_str = raw_event.get("start", {}).get("dateTime")
                end_str = raw_event.get("end", {}).get("dateTime")

            if not start_str or not end_str: return
            
            # Simple ISO parsing fallback
            try:
                # Remove Z and handle milliseconds if present
                from dateutil import parser
                start_time = parser.isoparse(start_str)
                end_time = parser.isoparse(end_str)
                # Ensure they have timezone info
                if start_time.tzinfo is None: start_time = start_time.replace(tzinfo=timezone.utc)
                if end_time.tzinfo is None: end_time = end_time.replace(tzinfo=timezone.utc)
            except Exception:
                logger.error(f"Date Parse Error: {start_str}")
                return

            # Check for existing
            stmt = select(EventTable).where(EventTable.user_id == user_id, EventTable.provider_id == ext_id)
            result = await db.execute(stmt)
            event = result.scalars().first()
            
            if not event:
                event = EventTable(
                    user_id=user_id,
                    provider_id=ext_id,
                    provider_source=source,
                    title=title,
                    is_busy=True, # Hard integration defaults to busy
                    category="meeting", # Categorize as meetings
                    color="#8A2BE2" if source == "google" else "#0078D4" 
                )
                db.add(event)
            
            # Update fields
            event.title = title
            event.start_time = start_time
            event.end_time = end_time
            event.description = raw_event.get("description") or raw_event.get("bodyPreview")
            
            await db.commit()
        except Exception as e:
            logger.error(f"Upsert Failed: {e}")
            await db.rollback()

sync_engine = SyncEngine()
