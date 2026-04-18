"""
Email to Calendar Parsing Service

Parses email content to extract meeting information and create calendar events.
Supports multiple email formats and meeting request patterns.
"""

import re
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EmailIntent(str, Enum):
    """Types of email intents related to scheduling."""

    MEETING_REQUEST = "meeting_request"
    MEETING_CONFIRMATION = "meeting_confirmation"
    MEETING_CANCELLATION = "meeting_cancellation"
    MEETING_RESCHEDULE = "meeting_reschedule"
    NO_ACTION = "no_action"


@dataclass
class ParsedMeeting:
    """Result of parsing an email for meeting information."""

    intent: EmailIntent
    title: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_minutes: int
    location: Optional[str]
    attendees: List[str]
    description: Optional[str]
    confidence: float
    extracted_text: str
    timezone: str = "UTC"


class EmailParserService:
    """Service for parsing emails and extracting meeting information."""

    # Time patterns
    TIME_PATTERNS = [
        r"(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)",
        r"(\d{1,2}):?(\d{2})?(am|pm)",
    ]

    # Date patterns
    DATE_PATTERNS = [
        r"\b(tomorrow|today|tonight|next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b",
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"((?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2})",
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{1,2}/\d{1,2}/\d{2,4})",
    ]

    # Duration patterns
    DURATION_PATTERNS = [
        r"(\d+)\s*(hour|hours|hr|hrs)",
        r"(\d+)\s*(minute|minutes|min|mins)",
        r"(\d+)\s*(half hour|half-hour)",
    ]

    # Meeting keywords
    MEETING_KEYWORDS = [
        "meet",
        "meeting",
        "sync",
        "call",
        "discussion",
        "chat",
        "talk",
        "conference",
        "review",
        "standup",
        "stand-up",
        "1:1",
        "one-on-one",
        "interview",
        "presentation",
        "demo",
        "workshop",
        "brainstorm",
    ]

    CONFIRMATION_KEYWORDS = [
        "confirmed",
        "accepted",
        "yes",
        "ill be there",
        "see you",
        "works for me",
        "sounds good",
        "im in",
        "count me in",
    ]

    CANCELLATION_KEYWORDS = [
        "cancel",
        "cancelled",
        "cant make it",
        "wont be able",
        "need to reschedule",
        "something came up",
        "unavailable",
    ]

    RESCHEDULE_KEYWORDS = [
        "reschedule",
        "move",
        "change",
        "different time",
        "another time",
        "wont work",
        "conflict",
        "overlap",
    ]

    def __init__(self):
        self.timezone = "UTC"

    async def parse_email(
        self,
        subject: str,
        body: str,
        sender: str,
        received_at: Optional[datetime] = None,
    ) -> ParsedMeeting:
        """Parse an email to extract meeting information."""
        if not received_at:
            received_at = datetime.now(timezone.utc)

        full_text = f"{subject} {body}"

        intent = self._detect_intent(full_text)
        title = self._extract_title(subject, body)
        start_time = self._extract_datetime(full_text, received_at)
        duration = self._extract_duration(full_text)
        location = self._extract_location(full_text)
        attendees = self._extract_attendees(body, sender)

        end_time = None
        if start_time:
            end_time = start_time + timedelta(minutes=duration)

        confidence = self._calculate_confidence(intent, title, start_time, location)

        return ParsedMeeting(
            intent=intent,
            title=title,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
            location=location,
            attendees=attendees,
            description=body[:500] if body else None,
            confidence=confidence,
            extracted_text=full_text[:1000],
            timezone=self.timezone,
        )

    def _detect_intent(self, text: str) -> EmailIntent:
        """Detect the scheduling intent of the email."""
        text_lower = text.lower()

        if any(keyword in text_lower for keyword in self.CANCELLATION_KEYWORDS):
            return EmailIntent.MEETING_CANCELLATION

        if any(keyword in text_lower for keyword in self.RESCHEDULE_KEYWORDS):
            return EmailIntent.MEETING_RESCHEDULE

        if any(keyword in text_lower for keyword in self.CONFIRMATION_KEYWORDS):
            return EmailIntent.MEETING_CONFIRMATION

        if any(keyword in text_lower for keyword in self.MEETING_KEYWORDS):
            return EmailIntent.MEETING_REQUEST

        return EmailIntent.NO_ACTION

    def _extract_title(self, subject: str, body: str) -> Optional[str]:
        """Extract meeting title from email."""
        title = subject.strip()

        prefixes_to_remove = [
            r"^re:\s*",
            r"^fw[d]?:\s*",
            r"^fwd:\s*",
            r"^meeting:\s*",
            r"^scheduled:\s*",
        ]

        for prefix in prefixes_to_remove:
            title = re.sub(prefix, "", title, flags=re.IGNORECASE)

        if len(title) < 10 or title.lower() in ["meeting", "sync", "call"]:
            body_patterns = [
                r"regarding\s*:?\s*([^.\n]+)",
                r"re:\s*([^.\n]+)",
                r"subject\s*:?\s*([^.\n]+)",
            ]

            for pattern in body_patterns:
                match = re.search(pattern, body, re.IGNORECASE)
                if match:
                    return match.group(1).strip()[:100]

        return title[:100] if title else None

    def _extract_datetime(
        self, text: str, reference_time: datetime
    ) -> Optional[datetime]:
        """Extract date and time from text."""
        text_lower = text.lower()
        base_date = reference_time.date()

        if "tomorrow" in text_lower:
            base_date = base_date + timedelta(days=1)
        elif "today" in text_lower or "tonight" in text_lower:
            base_date = base_date
        elif "next week" in text_lower:
            base_date = base_date + timedelta(days=7)

        days = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        for i, day in enumerate(days):
            if day in text_lower:
                current_weekday = reference_time.weekday()
                target_weekday = i
                days_ahead = target_weekday - current_weekday
                if days_ahead <= 0:
                    days_ahead += 7
                base_date = reference_time.date() + timedelta(days=days_ahead)
                break

        time_match = None
        for pattern in self.TIME_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                time_match = match
                break

        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0

            am_pm = time_match.group(3).lower() if time_match.group(3) else ""
            if am_pm == "pm" and hour != 12:
                hour += 12
            elif am_pm == "am" and hour == 12:
                hour = 0

            result = datetime.combine(
                base_date, datetime.min.time().replace(hour=hour, minute=minute)
            )
            return result.replace(tzinfo=timezone.utc)

        date_mentioned = any(
            re.search(pattern, text, re.IGNORECASE) for pattern in self.DATE_PATTERNS
        )

        if date_mentioned:
            result = datetime.combine(
                base_date, datetime.min.time().replace(hour=9, minute=0)
            )
            return result.replace(tzinfo=timezone.utc)

        return None

    def _extract_duration(self, text: str) -> int:
        """Extract meeting duration from text."""
        text_lower = text.lower()

        for pattern in self.DURATION_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                value = int(match.group(1))
                unit = match.group(2)

                if "hour" in unit or unit in ["hr", "hrs"]:
                    return value * 60
                elif "half hour" in unit:
                    return 30
                else:
                    return value

        if "standup" in text_lower or "stand-up" in text_lower:
            return 15
        elif "1:1" in text_lower or "one-on-one" in text_lower:
            return 30
        elif "sync" in text_lower:
            return 30
        elif "review" in text_lower:
            return 60
        elif "workshop" in text_lower:
            return 120

        return 30

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract meeting location from text."""
        text_lower = text.lower()

        if "zoom" in text_lower:
            return "Zoom"
        elif "teams" in text_lower or "microsoft" in text_lower:
            return "Microsoft Teams"
        elif "google meet" in text_lower or "meet" in text_lower:
            return "Google Meet"
        elif "webex" in text_lower:
            return "Webex"

        location_patterns = [
            r"(?:in|at|location|venue|place|room)\s+(?:the\s+)?([^.\n,]+?(?:room|hall|center|building|office)[^.\n,]*)",
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                location = re.sub(r"\s+", " ", location)
                return location[:100]

        return None

    def _extract_attendees(self, body: str, sender: str) -> List[str]:
        """Extract attendee emails from email body."""
        attendees = [sender]

        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        found_emails = re.findall(email_pattern, body)

        for email in found_emails:
            if email not in attendees:
                attendees.append(email)

        return attendees[:10]

    def _calculate_confidence(
        self,
        intent: EmailIntent,
        title: Optional[str],
        start_time: Optional[datetime],
        location: Optional[str],
    ) -> float:
        """Calculate confidence score for the parsed meeting."""
        score = 0.0

        if intent != EmailIntent.NO_ACTION:
            score += 20

        if title and len(title) > 5:
            score += 25

        if start_time:
            score += 30

        if location:
            score += 15

        if intent in [EmailIntent.MEETING_REQUEST, EmailIntent.MEETING_CONFIRMATION]:
            score += 10

        return min(score, 100.0)
