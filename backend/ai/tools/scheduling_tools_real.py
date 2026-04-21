"""
Production Scheduling Tools with Real Calendar API Integrations

Integrates with:
- Google Calendar API
- Microsoft Outlook Calendar
- Calendar availability checking
- Conflict detection
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy import select

from backend.utils.db import get_async_session_maker
from backend.models.tables import UserTokenTable, UserTable
from backend.services.token_encryption import decrypt_token_value
from backend.services.integrations.ms_graph import create_ms_event, update_ms_event
from backend.utils.logger import get_logger
from .registry import register_tool, ToolCategory, ToolPriority

logger = get_logger(__name__)


def _mask_email(email: Optional[str]) -> str:
    if not email or "@" not in email:
        return "<unknown>"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "**"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]


class CalendarConfig:
    """Calendar API configuration"""

    # Google Calendar
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CALENDAR_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback"
    )

    # Microsoft Outlook
    OUTLOOK_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID", "")
    OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET", "")
    OUTLOOK_TENANT_ID = os.getenv("OUTLOOK_TENANT_ID", "")

    @classmethod
    def is_outlook_configured(cls) -> bool:
        return bool(cls.OUTLOOK_CLIENT_ID and cls.OUTLOOK_CLIENT_SECRET)

    # Default calendar settings
    DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "America/New_York")
    DEFAULT_REMINDER_MINUTES = int(os.getenv("DEFAULT_REMINDER_MINUTES", "15"))

    @classmethod
    def is_google_configured(cls) -> bool:
        return bool(cls.GOOGLE_CLIENT_ID and cls.GOOGLE_CLIENT_SECRET)


# ═══════════════════════════════════════════════════════════════════
# GOOGLE CALENDAR SERVICE
# ═══════════════════════════════════════════════════════════════════


class GoogleCalendarService:
    """
    Google Calendar API Service

    Handles authentication and API calls for Google Calendar
    """

    def __init__(self, credentials_path: Optional[str] = None):
        self.service = None
        self.credentials = None
        self.credentials_path = credentials_path or "credentials.json"

    async def authenticate(self, user_email: str) -> bool:
        """
        Authenticate with Google Calendar API

        In production, this would use stored refresh tokens per user
        """
        try:
            # Load credentials from token file or create new
            creds = None
            token_path = f"tokens/{user_email}_token.json"

            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)

            # If no valid credentials, request new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # In production, redirect user to OAuth flow
                    # For now, log that auth is needed
                    logger.warning(f"Google Calendar auth required for {user_email}")
                    return False

                # Save credentials for future runs
                os.makedirs("tokens", exist_ok=True)
                with open(token_path, "w") as token:
                    token.write(creds.to_json())

            self.credentials = creds
            self.service = build("calendar", "v3", credentials=creds)

            return True

        except Exception as e:
            logger.error(f"Google Calendar authentication failed: {e}")
            return False

    async def create_event(
        self,
        title: str,
        start_time: str,
        duration_minutes: int,
        attendees: List[str],
        description: Optional[str] = None,
        location: Optional[str] = None,
        timezone: str = "UTC",
        reminders: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Create a calendar event in Google Calendar

        Returns:
            Event details including event_id and calendar_link
        """
        try:
            if not self.service:
                raise Exception("Not authenticated with Google Calendar")

            # Parse times
            start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end = start + timedelta(minutes=duration_minutes)

            # Build event body
            event_body = {
                "summary": title,
                "description": description,
                "location": location,
                "start": {
                    "dateTime": start.isoformat(),
                    "timeZone": timezone,
                },
                "end": {
                    "dateTime": end.isoformat(),
                    "timeZone": timezone,
                },
                "attendees": [{"email": email} for email in attendees],
                "reminders": {
                    "useDefault": False,
                    "overrides": reminders
                    or [
                        {"method": "email", "minutes": 24 * 60},  # 1 day before
                        {"method": "popup", "minutes": 15},  # 15 min before
                    ],
                },
                "guestsCanInviteOthers": False,
                "guestsCanModify": False,
                "guestsCanSeeOtherGuests": True,
            }

            # Create event
            event = (
                self.service.events()
                .insert(
                    calendarId="primary",
                    body=event_body,
                    sendUpdates="all",  # Send email invitations
                )
                .execute()
            )

            logger.info(f"Google Calendar event created: {event['id']}")

            return {
                "success": True,
                "event_id": event["id"],
                "calendar_link": event.get("htmlLink", ""),
                "title": title,
                "start_time": start_time,
                "attendees": attendees,
                "status": event.get("status", "confirmed"),
                "provider": "google_calendar",
            }

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return {"success": False, "error": str(e), "status": "failed"}
        except Exception as e:
            logger.error(f"Failed to create Google Calendar event: {e}")
            return {"success": False, "error": str(e), "status": "failed"}

    async def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        attendees: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing calendar event"""
        try:
            if not self.service:
                raise Exception("Not authenticated")

            # Get existing event
            event = (
                self.service.events()
                .get(calendarId="primary", eventId=event_id)
                .execute()
            )

            # Update fields
            if title:
                event["summary"] = title
            if description:
                event["description"] = description
            if start_time:
                start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                event["start"]["dateTime"] = start.isoformat()
                if duration_minutes:
                    end = start + timedelta(minutes=duration_minutes)
                    event["end"]["dateTime"] = end.isoformat()
            if attendees:
                event["attendees"] = [{"email": email} for email in attendees]

            # Update event
            updated_event = (
                self.service.events()
                .update(
                    calendarId="primary",
                    eventId=event_id,
                    body=event,
                    sendUpdates="all",
                )
                .execute()
            )

            return {
                "success": True,
                "event_id": updated_event["id"],
                "status": "updated",
                "provider": "google_calendar",
            }

        except Exception as e:
            logger.error(f"Failed to update Google Calendar event: {e}")
            return {"success": False, "error": str(e), "status": "failed"}

    async def delete_event(self, event_id: str) -> Dict[str, Any]:
        """Delete a calendar event"""
        try:
            if not self.service:
                raise Exception("Not authenticated")

            self.service.events().delete(
                calendarId="primary", eventId=event_id, sendUpdates="all"
            ).execute()

            return {
                "success": True,
                "event_id": event_id,
                "status": "deleted",
                "provider": "google_calendar",
            }

        except Exception as e:
            logger.error(f"Failed to delete Google Calendar event: {e}")
            return {"success": False, "error": str(e), "status": "failed"}

    async def check_availability(
        self, start_time: str, duration_minutes: int, timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Check if time slot is available

        Uses Google Calendar freebusy query
        """
        try:
            if not self.service:
                raise Exception("Not authenticated")

            start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end = start + timedelta(minutes=duration_minutes)

            body = {
                "timeMin": start.isoformat(),
                "timeMax": end.isoformat(),
                "timeZone": timezone,
                "items": [{"id": "primary"}],
            }

            result = self.service.freebusy().query(body=body).execute()

            calendars = result.get("calendars", {})
            primary = calendars.get("primary", {})
            busy = primary.get("busy", [])

            return {
                "success": True,
                "available": len(busy) == 0,
                "busy_slots": busy,
                "start_time": start_time,
                "duration_minutes": duration_minutes,
            }

        except Exception as e:
            logger.error(f"Failed to check availability: {e}")
            return {"success": False, "available": False, "error": str(e)}

    async def find_available_slots(
        self,
        date: str,
        duration_minutes: int,
        timezone: str = "UTC",
        start_hour: int = 9,
        end_hour: int = 17,
    ) -> List[Dict[str, Any]]:
        """
        Find available time slots for a given date

        Checks availability in 30-minute increments
        """
        try:
            if not self.service:
                raise Exception("Not authenticated")

            available_slots = []
            base_date = datetime.fromisoformat(date).date()

            # Check every 30 minutes during business hours
            for hour in range(start_hour, end_hour):
                for minute in [0, 30]:
                    slot_start = datetime.combine(
                        base_date, datetime.min.time().replace(hour=hour, minute=minute)
                    )
                    slot_time = slot_start.isoformat()

                    availability = await self.check_availability(
                        slot_time, duration_minutes, timezone
                    )

                    if availability.get("available"):
                        available_slots.append(
                            {
                                "start_time": slot_time,
                                "end_time": (
                                    slot_start + timedelta(minutes=duration_minutes)
                                ).isoformat(),
                                "duration_minutes": duration_minutes,
                            }
                        )

            return available_slots

        except Exception as e:
            logger.error(f"Failed to find available slots: {e}")
            return []


# ═══════════════════════════════════════════════════════════════════
# PUBLIC TOOL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════


def _normalize_calendar_provider(provider: str) -> str:
    provider = (provider or "").strip().lower()
    if provider in {"outlook", "microsoft_outlook", "microsoft_365"}:
        return "microsoft"
    if provider in {"google_meet", "google_calendar"}:
        return "google"
    return provider or "google"


async def _get_oauth_token_data_for_email(
    user_email: Optional[str], provider: str
) -> Optional[dict]:
    if not user_email or provider != "microsoft":
        return None

    session_factory = get_async_session_maker()
    async with session_factory() as session:
        stmt = select(UserTable).where(UserTable.email == user_email)
        user = (await session.execute(stmt)).scalars().first()
        if not user:
            return None

        token_stmt = select(UserTokenTable).where(
            UserTokenTable.user_id == user.id,
            UserTokenTable.provider == provider,
            UserTokenTable.is_active == True,
        )
        token = (await session.execute(token_stmt)).scalars().first()
        if not token:
            return None

        access_token, _ = decrypt_token_value(token.access_token)
        refresh_token, _ = decrypt_token_value(token.refresh_token)
        if not access_token or not refresh_token:
            return None

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "scopes": token.scopes,
        }


@register_tool(
    name="create_calendar_event",
    description="Create a calendar event using Google or Microsoft Calendar APIs",
    category=ToolCategory.SCHEDULING,
    priority=ToolPriority.CRITICAL,
)
async def create_calendar_event(
    title: str,
    start_time: str,
    duration_minutes: int,
    attendees: List[str],
    description: Optional[str] = None,
    location: Optional[str] = None,
    timezone: str = "UTC",
    organizer_email: Optional[str] = None,
    calendar_provider: str = "google",
) -> Dict[str, Any]:
    """
    Create a calendar event with real API integration

    Args:
        title: Event title
        start_time: ISO format start time
        duration_minutes: Duration in minutes
        attendees: List of attendee emails
        description: Event description
        location: Location or video link
        timezone: Timezone (default UTC)
        organizer_email: Organizer's email (for auth)
        calendar_provider: 'google' or 'outlook'

    Returns:
        Event creation result
    """
    try:
        calendar_provider = _normalize_calendar_provider(calendar_provider)

        if calendar_provider == "google":
            if not CalendarConfig.is_google_configured():
                logger.warning("Google Calendar not configured - logging event only")
                return {
                    "success": True,
                    "event_id": f"dev_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "title": title,
                    "start_time": start_time,
                    "duration_minutes": duration_minutes,
                    "attendees": attendees,
                    "calendar_link": "https://calendar.google.com/calendar/event?eid=dev",
                    "status": "logged",
                    "mode": "development",
                    "provider": calendar_provider,
                }

            # Use Google Calendar
            calendar = GoogleCalendarService()
            auth_success = await calendar.authenticate(
                organizer_email or "default@graftai.com"
            )

            if not auth_success:
                return {
                    "success": True,
                    "event_id": f"dev_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "title": title,
                    "start_time": start_time,
                    "duration_minutes": duration_minutes,
                    "attendees": attendees,
                    "calendar_link": "https://calendar.google.com",
                    "status": "logged",
                    "mode": "development",
                    "message": "Calendar auth required - event logged for manual creation",
                }

            result = await calendar.create_event(
                title=title,
                start_time=start_time,
                duration_minutes=duration_minutes,
                attendees=attendees,
                description=description,
                location=location,
                timezone=timezone,
            )

            return result

        elif calendar_provider == "microsoft":
            token_data = await _get_oauth_token_data_for_email(
                organizer_email, "microsoft"
            )
            if not token_data:
                logger.warning(
                    "Microsoft Outlook token not found for organizer_email=%s",
                    organizer_email,
                )
                return {
                    "success": False,
                    "error": "Microsoft Outlook not configured for this organizer",
                    "status": "failed",
                }

            event_details = {
                "title": title,
                "description": description,
                "start_time": datetime.fromisoformat(start_time.replace("Z", "+00:00")),
                "end_time": datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                + timedelta(minutes=duration_minutes),
                "attendees": attendees,
                "timezone": timezone,
                "is_meeting": True,
            }

            result = await create_ms_event(token_data, event_details)
            meeting_url = (
                result.get("onlineMeeting", {}).get("joinUrl")
                or result.get("webLink")
                or result.get("joinWebUrl")
                or result.get("joinUrl")
            )
            return {
                "success": True,
                "event_id": result.get("id"),
                "calendar_link": meeting_url,
                "title": title,
                "start_time": start_time,
                "attendees": attendees,
                "status": "confirmed",
                "provider": "microsoft",
            }

        else:
            return {
                "success": False,
                "error": f"Unknown calendar provider: {calendar_provider}",
                "status": "failed",
            }

    except Exception as e:
        logger.error(f"Failed to create calendar event: {e}")
        return {"success": False, "error": str(e), "status": "failed"}


@register_tool(
    name="update_calendar_event",
    description="Update an existing calendar event",
    category=ToolCategory.SCHEDULING,
    priority=ToolPriority.HIGH,
)
async def update_calendar_event(
    event_id: str,
    title: Optional[str] = None,
    start_time: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    attendees: Optional[List[str]] = None,
    organizer_email: Optional[str] = None,
    calendar_provider: str = "google",
) -> Dict[str, Any]:
    """Update an existing calendar event"""
    try:
        calendar_provider = _normalize_calendar_provider(calendar_provider)

        if calendar_provider == "google":
            if not CalendarConfig.is_google_configured():
                logger.warning("Google Calendar not configured - logging update only")
                return {
                    "success": True,
                    "event_id": event_id,
                    "status": "logged",
                    "mode": "development",
                }

            calendar = GoogleCalendarService()
            await calendar.authenticate(organizer_email or "default@graftai.com")

            return await calendar.update_event(
                event_id=event_id,
                title=title,
                start_time=start_time,
                duration_minutes=duration_minutes,
                attendees=attendees,
            )

        elif calendar_provider == "microsoft":
            token_data = await _get_oauth_token_data_for_email(
                organizer_email, "microsoft"
            )
            if not token_data:
                logger.warning(
                    "Microsoft Outlook token not found for organizer_email=%s",
                    _mask_email(organizer_email),
                )
                return {
                    "success": False,
                    "error": "Microsoft Outlook not configured for this organizer",
                    "status": "failed",
                }

            event_details = {
                "title": title,
                "description": None,
                "start_time": None,
                "end_time": None,
                "attendees": attendees or [],
            }
            if start_time:
                event_details["start_time"] = datetime.fromisoformat(
                    start_time.replace("Z", "+00:00")
                )
            if duration_minutes and start_time:
                event_details["end_time"] = datetime.fromisoformat(
                    start_time.replace("Z", "+00:00")
                ) + timedelta(minutes=duration_minutes)
            if title is not None:
                event_details["title"] = title
            if attendees is not None:
                event_details["attendees"] = attendees

            result = await update_ms_event(token_data, event_id, event_details)
            meeting_url = (
                result.get("onlineMeeting", {}).get("joinUrl")
                or result.get("webLink")
                or result.get("joinWebUrl")
                or result.get("joinUrl")
            )
            return {
                "success": True,
                "event_id": event_id,
                "meeting_url": meeting_url,
                "status": "updated",
                "provider": "microsoft",
            }

        return {
            "success": False,
            "error": "Calendar provider not supported",
            "status": "failed",
        }

    except Exception as e:
        logger.error(f"Failed to update calendar event: {e}")
        return {"success": False, "error": str(e), "status": "failed"}


@register_tool(
    name="check_calendar_availability",
    description="Check if a time slot is available in the calendar",
    category=ToolCategory.SCHEDULING,
    priority=ToolPriority.HIGH,
)
async def check_calendar_availability(
    start_time: str,
    duration_minutes: int,
    timezone: str = "UTC",
    organizer_email: Optional[str] = None,
) -> Dict[str, Any]:
    """Check if a time slot is available"""
    try:
        if not CalendarConfig.is_google_configured():
            logger.warning("Calendar not configured - assuming available")
            return {
                "success": True,
                "available": True,
                "busy_slots": [],
                "mode": "development",
            }

        calendar = GoogleCalendarService()
        await calendar.authenticate(organizer_email or "default@graftai.com")

        return await calendar.check_availability(
            start_time=start_time, duration_minutes=duration_minutes, timezone=timezone
        )

    except Exception as e:
        logger.error(f"Failed to check availability: {e}")
        return {"success": False, "available": False, "error": str(e)}


@register_tool(
    name="search_available_slots",
    description="Find available time slots for a meeting",
    category=ToolCategory.SCHEDULING,
    priority=ToolPriority.HIGH,
)
async def search_available_slots(
    date: str,
    duration_minutes: int,
    timezone: str = "UTC",
    organizer_email: Optional[str] = None,
    start_hour: int = 9,
    end_hour: int = 17,
) -> List[Dict[str, Any]]:
    """Find available time slots"""
    try:
        if not CalendarConfig.is_google_configured():
            logger.warning("Calendar not configured - returning mock slots")
            # Return mock slots for development
            base_date = datetime.fromisoformat(date).date()
            return [
                {
                    "start_time": datetime.combine(
                        base_date, datetime.min.time().replace(hour=10, minute=0)
                    ).isoformat(),
                    "end_time": datetime.combine(
                        base_date, datetime.min.time().replace(hour=10, minute=30)
                    ).isoformat(),
                    "duration_minutes": duration_minutes,
                    "mode": "development",
                },
                {
                    "start_time": datetime.combine(
                        base_date, datetime.min.time().replace(hour=14, minute=0)
                    ).isoformat(),
                    "end_time": datetime.combine(
                        base_date, datetime.min.time().replace(hour=14, minute=30)
                    ).isoformat(),
                    "duration_minutes": duration_minutes,
                    "mode": "development",
                },
            ]

        calendar = GoogleCalendarService()
        await calendar.authenticate(organizer_email or "default@graftai.com")

        return await calendar.find_available_slots(
            date=date,
            duration_minutes=duration_minutes,
            timezone=timezone,
            start_hour=start_hour,
            end_hour=end_hour,
        )

    except Exception as e:
        logger.error(f"Failed to search available slots: {e}")
        return []


@register_tool(
    name="get_conflicts",
    description="Detect calendar conflicts for a proposed time slot",
    category=ToolCategory.SCHEDULING,
    priority=ToolPriority.HIGH,
)
async def get_conflicts(
    start_time: str,
    duration_minutes: int,
    attendees: List[str],
    organizer_email: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Detect conflicts with existing calendar events

    Returns list of conflicting events with details
    """
    try:
        if not CalendarConfig.is_google_configured():
            logger.warning("Calendar not configured - assuming no conflicts")
            return []

        calendar = GoogleCalendarService()
        await calendar.authenticate(organizer_email or "default@graftai.com")

        availability = await calendar.check_availability(
            start_time=start_time, duration_minutes=duration_minutes
        )

        conflicts = availability.get("busy_slots", [])

        return [
            {
                "start": conflict.get("start"),
                "end": conflict.get("end"),
                "severity": "high" if conflict.get("start") == start_time else "medium",
            }
            for conflict in conflicts
        ]

    except Exception as e:
        logger.error(f"Failed to get conflicts: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════


async def generate_google_auth_url(redirect_uri: Optional[str] = None) -> str:
    """
    Generate Google OAuth URL for calendar authorization

    Returns:
        URL to redirect user to for authorization
    """
    if not CalendarConfig.is_google_configured():
        raise Exception("Google Calendar not configured")

    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json",
        SCOPES,
        redirect_uri=redirect_uri or CalendarConfig.GOOGLE_REDIRECT_URI,
    )

    auth_url, _ = flow.authorization_url(prompt="consent")

    return auth_url


async def handle_google_callback(code: str, user_email: str) -> bool:
    """
    Handle Google OAuth callback and store credentials

    Args:
        code: Authorization code from callback
        user_email: User email for token storage

    Returns:
        Success status
    """
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES, redirect_uri=CalendarConfig.GOOGLE_REDIRECT_URI
        )

        flow.fetch_token(code=code)
        creds = flow.credentials

        # Save token for user
        token_path = f"tokens/{user_email}_token.json"
        os.makedirs("tokens", exist_ok=True)

        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

        logger.info(f"Google Calendar auth stored for {user_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to handle Google callback: {e}")
        return False


async def revoke_google_auth(user_email: str) -> bool:
    """Revoke Google Calendar authorization for a user"""
    try:
        token_path = f"tokens/{user_email}_token.json"

        if os.path.exists(token_path):
            # Load credentials and revoke
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

            import requests

            requests.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": creds.token},
                headers={"content-type": "application/x-www-form-urlencoded"},
            )

            # Delete token file
            os.remove(token_path)

            logger.info(f"Google Calendar auth revoked for {user_email}")
            return True

        return False

    except Exception as e:
        logger.error(f"Failed to revoke Google auth: {e}")
        return False
