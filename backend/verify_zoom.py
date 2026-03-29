import os
import asyncio
import base64
from unittest.mock import AsyncMock, patch
from services.zoom import ZoomService

async def test_zoom_service_logic():
    # Setup mock environment
    os.environ["ZOOM_CLIENT_ID"] = "test_client_id"
    os.environ["ZOOM_CLIENT_SECRET"] = "test_client_secret"
    os.environ["ZOOM_ACCOUNT_ID"] = "test_account_id"
    
    service = ZoomService()
    
    print("--- Verifying Auth Header ---")
    auth_header = service._get_auth_header()
    expected_auth = base64.b64encode(b"test_client_id:test_client_id").decode() # Wait, typo in my thought? No, based on code logic.
    # Actually client_id:client_secret
    expected_val = base64.b64encode(b"test_client_id:test_client_secret").decode()
    assert auth_header == f"Basic {expected_val}"
    print("✅ Auth header matches expected Basic Base64 format.")

    print("\n--- Verifying Token Retrieval (Mocked) ---")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "mock_access_token",
            "expires_in": 3600
        }
        
        token = await service.get_access_token(force_refresh=True)
        assert token == "mock_access_token"
        print("✅ Token retrieval logic works correctly.")

    print("\n--- Verifying Meeting Creation (Mocked) ---")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "id": 123456789,
            "topic": "Test Meeting",
            "join_url": "https://zoom.us/j/123456789"
        }
        
        # Patching get_access_token to return our mock token
        with patch.object(ZoomService, "get_access_token", return_value="mock_token"):
            meeting = await service.create_meeting("Test Meeting", "2026-03-31T10:00:00Z")
            assert meeting["id"] == 123456789
            assert meeting["join_url"] == "https://zoom.us/j/123456789"
            print("✅ Meeting creation payload and response handling works.")

    print("\n🎉 All internal Zoom service logic tests passed!")

if __name__ == "__main__":
    asyncio.run(test_zoom_service_logic())
