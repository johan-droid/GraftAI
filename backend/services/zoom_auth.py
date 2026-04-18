import os
from authlib.integrations.httpx_client import AsyncOAuth2Client

ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")

# Use the backend base URL provided through environment variables.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
ZOOM_REDIRECT_URI = os.getenv(
    "ZOOM_REDIRECT_URI", f"{BACKEND_URL}/api/v1/auth/zoom/callback"
)

if not ZOOM_CLIENT_ID or not ZOOM_CLIENT_SECRET:
    import logging

    logging.warning(
        "⚠️  Zoom OAuth not fully configured. Set ZOOM_CLIENT_ID and ZOOM_CLIENT_SECRET to enable Zoom login."
    )

SCOPES = "meeting:write user:read"


async def get_zoom_auth_url(state: str):
    if not ZOOM_CLIENT_ID or not ZOOM_CLIENT_SECRET:
        raise ValueError(
            "Zoom OAuth is not configured. Set ZOOM_CLIENT_ID and ZOOM_CLIENT_SECRET in your .env file."
        )

    client = AsyncOAuth2Client(
        client_id=ZOOM_CLIENT_ID,
        client_secret=ZOOM_CLIENT_SECRET,
        scope=SCOPES,
        redirect_uri=ZOOM_REDIRECT_URI,
    )
    authorization_url, _ = client.create_authorization_url(
        "https://zoom.us/oauth/authorize",
        state=state,
        access_type="offline",
        prompt="consent",
    )
    return authorization_url


async def fetch_zoom_tokens(code: str):
    if not ZOOM_CLIENT_ID or not ZOOM_CLIENT_SECRET:
        raise ValueError(
            "Zoom OAuth is not configured. Set ZOOM_CLIENT_ID and ZOOM_CLIENT_SECRET in your .env file."
        )

    async with AsyncOAuth2Client(
        client_id=ZOOM_CLIENT_ID,
        client_secret=ZOOM_CLIENT_SECRET,
    ) as client:
        token = await client.fetch_token(
            "https://zoom.us/oauth/token",
            code=code,
            grant_type="authorization_code",
            redirect_uri=ZOOM_REDIRECT_URI,
        )
        resp = await client.get("https://api.zoom.us/v2/users/me")
        profile = resp.json()
    return {
        "email": profile.get("email"),
        "full_name": profile.get("first_name") + " " + profile.get("last_name")
        if profile.get("first_name") and profile.get("last_name")
        else profile.get("email"),
        "token": token,
    }
