import os
from typing import Optional
from authlib.integrations.httpx_client import AsyncOAuth2Client

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Use the backend base URL provided through environment variables.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", f"{BACKEND_URL}/api/v1/auth/google/callback")

# Validate Google OAuth configuration
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    import logging
    logging.warning(
        "⚠️  Google OAuth not fully configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to enable Google login. "
        "Visit https://console.cloud.google.com to create OAuth 2.0 credentials."
    )

SCOPES = "openid profile email https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events"

async def get_google_auth_url(state: str, prompt: Optional[str] = None):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError(
            "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file. "
            "Get credentials from: https://console.cloud.google.com/apis/credentials"
        )
    
    client = AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scope=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    auth_params = {
        "state": state,
        "access_type": "offline",
    }
    if prompt:
        auth_params["prompt"] = prompt

    authorization_url, _ = client.create_authorization_url(
        "https://accounts.google.com/o/oauth2/v2/auth",
        **auth_params
    )
    return authorization_url

async def fetch_google_tokens(code: str):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise ValueError(
            "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file. "
            "Get credentials from: https://console.cloud.google.com/apis/credentials"
        )
    
    async with AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    ) as client:
        token = await client.fetch_token(
            "https://oauth2.googleapis.com/token",
            code=code,
            grant_type="authorization_code",
            redirect_uri=GOOGLE_REDIRECT_URI,
            headers={"Accept": "application/json"},
        )
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        profile = resp.json()
    return {
        "email": profile.get("email"),
        "full_name": profile.get("name"),
        "token": token
    }
