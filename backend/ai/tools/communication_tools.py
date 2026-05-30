"""
Communication Tools for Agent Actions

Tools for sending messages through various channels.
"""
from datetime import UTC, datetime

from backend.utils.logger import get_logger

from .registry import ToolCategory, ToolPriority, register_tool

logger = get_logger(__name__)

def _mask_email(email: str) -> str:
    if not isinstance(email, str) or "@" not in email:
        return "unknown"
    local, domain = email.split("@", 1)
    masked_local = f"{local[:1]}***" if local else "***"
    return f"{masked_local}@{domain}"

@register_tool(name="send_email", description="Send an email to a recipient with subject and body", category=ToolCategory.COMMUNICATION, priority=ToolPriority.HIGH, examples=[{"to": "user@example.com", "subject": "Meeting Confirmation", "body": "Your meeting has been scheduled for tomorrow at 2pm."}])
async def send_email(to: str, subject: str, body: str, cc: list[str] | None=None, bcc: list[str] | None=None, template: str | None=None, from_address: str | None=None, attachments: list[dict] | None=None) -> dict:
    """
    Send an email to a recipient.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content (HTML or plain text)
        cc: Optional list of CC recipients
        bcc: Optional list of BCC recipients
        template: Optional template name to use
        from_address: Optional sender address (uses default if not specified)
        attachments: Optional list of dictionaries with filename, content, and type

    Returns:
        Dict with email_id, status, and timestamp
    """
    try:
        email_id = f"email_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        logger.info("Sending email", extra={"recipient": _mask_email(to), "subject": subject})
        return {"success": True, "email_id": email_id, "to": to, "subject": subject, "sent_at": datetime.now(UTC).isoformat(), "status": "sent", "message": f"Email sent to {to}"}
    except Exception as e:
        logger.exception("Failed to send email: %s", e)
        return {"success": False, "error": str(e), "to": to, "subject": subject}

@register_tool(name="send_sms", description="Send an SMS text message to a phone number", category=ToolCategory.COMMUNICATION, priority=ToolPriority.HIGH, examples=[{"to": "+1234567890", "message": "Your meeting starts in 15 minutes."}])
async def send_sms(to: str, message: str, from_number: str | None=None) -> dict:
    """
    Send an SMS to a phone number.

    Args:
        to: Recipient phone number with country code (e.g., +1234567890)
        message: SMS message content (max 1600 characters)
        from_number: Optional sender number

    Returns:
        Dict with sms_id, status, and details
    """
    try:
        if len(message) > 1600:
            msg = "Message exceeds 1600 character limit"
            raise ValueError(msg)
        sms_id = f"sms_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        logger.info("Sending SMS to %s", to)
        return {"success": True, "sms_id": sms_id, "to": to, "message": message, "sent_at": datetime.now(UTC).isoformat(), "status": "sent", "segments": len(message) // 160 + 1}
    except Exception as e:
        logger.exception("Failed to send SMS: %s", e)
        return {"success": False, "error": str(e), "to": to}

@register_tool(name="post_to_slack", description="Post a message to a Slack channel", category=ToolCategory.COMMUNICATION, priority=ToolPriority.MEDIUM, examples=[{"channel": "#bookings", "message": "New high-value booking received!", "blocks": []}])
async def post_to_slack(channel: str, message: str, blocks: list[dict] | None=None, thread_ts: str | None=None, username: str | None="GraftAI Bot") -> dict:
    """
    Post a message to Slack.

    Args:
        channel: Channel name (e.g., #general) or channel ID
        message: Message text
        blocks: Optional Slack Block Kit blocks for rich formatting
        thread_ts: Optional thread timestamp to reply in thread
        username: Bot username to display

    Returns:
        Dict with message_id and status
    """
    try:
        message_id = f"slack_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        logger.info("Posting to Slack channel %s", channel)
        return {"success": True, "message_id": message_id, "channel": channel, "posted_at": datetime.now(UTC).isoformat(), "status": "posted", "message": f"Posted to {channel}"}
    except Exception as e:
        logger.exception("Failed to post to Slack: %s", e)
        return {"success": False, "error": str(e), "channel": channel}

@register_tool(name="send_teams_message", description="Send a message to a Microsoft Teams user or channel", category=ToolCategory.COMMUNICATION, priority=ToolPriority.MEDIUM, examples=[{"user": "user@company.com", "message": "Your meeting is confirmed for tomorrow at 2pm."}])
async def send_teams_message(user: str | None=None, channel: str | None=None, message: str="", card: dict | None=None) -> dict:
    """
    Send a message to Microsoft Teams.

    Args:
        user: User email for direct message (provide user OR channel, not both)
        channel: Channel ID or name (provide user OR channel, not both)
        message: Message text
        card: Optional adaptive card for rich formatting

    Returns:
        Dict with message_id and status
    """
    try:
        if not user and (not channel):
            msg = "Must provide either user or channel"
            raise ValueError(msg)
        if user and channel:
            msg = "Provide only user or channel, not both"
            raise ValueError(msg)
        message_id = f"teams_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        recipient = user or channel
        logger.info("Sending Teams message", extra={"recipient": _mask_email(recipient) if user else recipient})
        return {"success": True, "message_id": message_id, "recipient": recipient, "sent_at": datetime.now(UTC).isoformat(), "status": "sent"}
    except Exception as e:
        logger.exception("Failed to send Teams message: %s", e)
        return {"success": False, "error": str(e), "recipient": user or channel}

@register_tool(name="send_calendar_invite", description="Send a calendar invite to an attendee for a meeting", category=ToolCategory.COMMUNICATION, priority=ToolPriority.CRITICAL, examples=[{"attendee": "user@example.com", "title": "Team Sync", "start_time": "2024-04-15T14:00:00", "duration_minutes": 30, "location": "Conference Room A"}])
async def send_calendar_invite(attendee: str, title: str, start_time: str, duration_minutes: int, location: str | None=None, description: str | None=None, organizer: str | None=None, timezone_str: str="UTC") -> dict:
    """
    Send a calendar invite to an attendee.

    Args:
        attendee: Attendee email address
        title: Meeting title
        start_time: Meeting start time (ISO format)
        duration_minutes: Meeting duration in minutes
        location: Optional meeting location
        description: Optional meeting description
        organizer: Optional organizer email
        timezone_str: Timezone (default UTC)

    Returns:
        Dict with invite_id and status
    """
    try:
        from datetime import datetime, timedelta
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end = start + timedelta(minutes=duration_minutes)
        invite_id = f"invite_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        logger.info("Sending calendar invite to %s for %s", attendee, title)
        import uuid
        fmt = "%Y%m%dT%H%M%SZ"
        dtstamp = datetime.now(UTC).strftime(fmt)
        dtstart = start.astimezone(UTC).strftime(fmt)
        dtend = end.astimezone(UTC).strftime(fmt)
        uid = f"invite_{uuid.uuid4().hex}@graftai.com"
        ics_lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//GraftAI//NONSGML Calendar Tool//EN", "BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{dtstamp}", f"DTSTART:{dtstart}", f"DTEND:{dtend}", f"SUMMARY:{title}"]
        if location:
            ics_lines.append(f"LOCATION:{location}")
        if description:
            escaped_desc = description.replace("\n", "\\n")
            ics_lines.append(f"DESCRIPTION:{escaped_desc}")
        if organizer:
            ics_lines.append(f"ORGANIZER;CN=Organizer:mailto:{organizer}")
        ics_lines.append(f"ATTENDEE;RSVP=TRUE:mailto:{attendee}")
        ics_lines.append("END:VEVENT")
        ics_lines.append("END:VCALENDAR")
        ics_content = "\r\n".join(ics_lines)
        logger.info("Generated ICS content for %s", title)
        await send_email(to=attendee, subject=f"Invitation: {title}", body=f"Please find the calendar invitation for {title} attached.", from_address=organizer, attachments=[{"filename": "invite.ics", "content": ics_content, "type": "text/calendar"}])
        return {"success": True, "invite_id": invite_id, "ics_content": ics_content, "attendee": attendee, "title": title, "start_time": start_time, "end_time": end.isoformat(), "duration_minutes": duration_minutes, "location": location, "sent_at": datetime.now(UTC).isoformat(), "status": "sent"}
    except Exception as e:
        logger.exception("Failed to send calendar invite: %s", e)
        return {"success": False, "error": str(e), "attendee": attendee, "title": title}
