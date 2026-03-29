import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta, timezone

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

@pytest.mark.asyncio
async def test_meeting_link_generation():
    from backend.services.scheduler import _generate_meeting_link  # type: ignore
    
    start = datetime.now(timezone.utc)
    end = start + timedelta(hours=1)
    
    # Test 1: Simulated Google Meet Link (No token)
    link_sim_google = await _generate_meeting_link("google_meet", 1, "Test Google", start, end, access_token=None)
    print(f"Simulated Google link: {link_sim_google}")
    assert "meet.google.com" in link_sim_google
    
    class MockResponseGoogle:
        status_code = 200
        def json(self):
            return {"hangoutLink": "https://meet.google.com/abc-defg-hij"}
            
    # Test 2: Real Google Meet Link (Mocked API)
    with patch("backend.services.google_calendar.httpx.AsyncClient") as mock_httpx_google:
        mock_client = AsyncMock()
        mock_httpx_google.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = MockResponseGoogle()
        
        link_real_google = await _generate_meeting_link("google_meet", 1, "Test Google", start, end, access_token="fake-google-token")
        print(f"Real Google link: {link_real_google}")
        assert link_real_google == "https://meet.google.com/abc-defg-hij"

    # Test 3: Simulated Teams Link (No token)
    link_sim_teams = await _generate_meeting_link("teams", 1, "Test Teams", start, end, access_token=None)
    print(f"Simulated Teams link: {link_sim_teams}")
    assert "teams.microsoft.com" in link_sim_teams

    class MockResponseTeams:
        status_code = 201
        def json(self):
            return {"onlineMeeting": {"joinUrl": "https://teams.microsoft.com/l/meetup-join/abc-123"}}

    # Test 4: Real Teams Link (Mocked API)
    with patch("backend.services.microsoft_calendar.httpx.AsyncClient") as mock_httpx_ms:
        mock_client = AsyncMock()
        mock_httpx_ms.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = MockResponseTeams()
        
        link_real_teams = await _generate_meeting_link("teams", 1, "Test Teams", start, end, access_token="fake-ms-token")
        print(f"Real Teams link: {link_real_teams}")
        assert link_real_teams == "https://teams.microsoft.com/l/meetup-join/abc-123"

    print("✅ All tests passed!")
