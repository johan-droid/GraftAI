import pytest
from unittest.mock import patch, AsyncMock
from backend.ai.tools.communication_tools import send_calendar_invite

@pytest.mark.asyncio
@patch("backend.ai.tools.communication_tools.send_email", new_callable=AsyncMock)
async def test_send_calendar_invite(mock_send_email):
    mock_send_email.return_value = {"success": True}

    result = await send_calendar_invite(
        attendee="test@example.com",
        title="Test Sync",
        start_time="2024-04-15T14:00:00Z",
        duration_minutes=45,
        location="Zoom",
        description="Let's sync",
        organizer="org@example.com"
    )

    assert result["success"] is True
    assert result["attendee"] == "test@example.com"
    assert result["title"] == "Test Sync"
    assert "ics_content" in result

    ics = result["ics_content"]
    assert "BEGIN:VCALENDAR" in ics
    assert "SUMMARY:Test Sync" in ics
    assert "LOCATION:Zoom" in ics
    assert "DESCRIPTION:Let's sync" in ics
    assert "ORGANIZER;CN=Organizer:mailto:org@example.com" in ics
    assert "ATTENDEE;RSVP=TRUE:mailto:test@example.com" in ics
    assert "DTSTART:20240415T140000Z" in ics
    assert "DTEND:20240415T144500Z" in ics

    # Assert email was sent with ICS attachment
    mock_send_email.assert_called_once()
    kwargs = mock_send_email.call_args.kwargs
    assert kwargs["to"] == "test@example.com"
    assert "attachments" in kwargs
    assert len(kwargs["attachments"]) == 1
    assert kwargs["attachments"][0]["filename"] == "invite.ics"
    assert "BEGIN:VCALENDAR" in kwargs["attachments"][0]["content"]
    assert kwargs["attachments"][0]["type"] == "text/calendar"
