import os
from typing import Optional
from authlib.integrations.httpx_client import AsyncOAuth2Client
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Load dotenv from backend folder if available so imported service code can work
# outside of the main application startup path.
backend_dir = Path(__file__).resolve().parents[1]
for dotenv_file in [".env", ".env.local", ".env.development", ".env.development.local"]:
    path = backend_dir / dotenv_file
    if path.exists():
        load_dotenv(dotenv_path=path, override=False)

def _resolve_google_oauth_credentials() -> tuple[Optional[str], Optional[str]]:
    client_id = (
        os.getenv("GOOGLE_CLIENT_ID")
        or os.getenv("GOOGLE_ID")
        or os.getenv("NEXTAUTH_GOOGLE_ID")
        or os.getenv("AUTH_GOOGLE_ID")
    )
    client_secret = (
        os.getenv("GOOGLE_CLIENT_SECRET")
        or os.getenv("GOOGLE_SECRET")
        or os.getenv("NEXTAUTH_GOOGLE_SECRET")
        or os.getenv("AUTH_GOOGLE_SECRET")
    )
    return client_id, client_secret

# Use the backend base URL provided through environment variables.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", f"{BACKEND_URL}/api/v1/auth/google/callback"
)

# Validate Google OAuth configuration on import, useful for early warnings.
if not _resolve_google_oauth_credentials()[0] or not _resolve_google_oauth_credentials()[1]:
    import logging

    logging.warning(
        "⚠️  Google OAuth not fully configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
        "or GOOGLE_ID and GOOGLE_SECRET or NEXTAUTH_GOOGLE_ID and NEXTAUTH_GOOGLE_SECRET "
        "or AUTH_GOOGLE_ID and AUTH_GOOGLE_SECRET in your environment. "
        "Visit https://console.cloud.google.com/apis/credentials"
    )

SCOPES = "openid profile email https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events"


async def get_google_auth_url(state: str, prompt: Optional[str] = None):
    client_id, client_secret = _resolve_google_oauth_credentials()
    if not client_id or not client_secret:
        raise ValueError(
            "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
            "or GOOGLE_ID and GOOGLE_SECRET or NEXTAUTH_GOOGLE_ID and NEXTAUTH_GOOGLE_SECRET "
            "or AUTH_GOOGLE_ID and AUTH_GOOGLE_SECRET in your environment. "
            "Get credentials from: https://console.cloud.google.com/apis/credentials"
        )

    client = AsyncOAuth2Client(
        client_id=client_id,
        client_secret=client_secret,
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
        "https://accounts.google.com/o/oauth2/v2/auth", **auth_params
    )
    return authorization_url


async def fetch_google_tokens(code: str):
    client_id, client_secret = _resolve_google_oauth_credentials()
    if not client_id or not client_secret:
        raise ValueError(
            "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
            "or GOOGLE_ID and GOOGLE_SECRET or NEXTAUTH_GOOGLE_ID and NEXTAUTH_GOOGLE_SECRET "
            "or AUTH_GOOGLE_ID and AUTH_GOOGLE_SECRET in your environment. "
            "Get credentials from: https://console.cloud.google.com/apis/credentials"
        )

    async with AsyncOAuth2Client(
        client_id=client_id,
        client_secret=client_secret,
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
        "token": token,
    }


async def verify_google_token(access_token: str) -> dict:
    if not access_token:
        raise ValueError("No access token provided")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        if resp.status_code != 200:
            raise ValueError("Invalid Google access token")
        profile = resp.json()
        return {
            "email": profile.get("email"),
            "full_name": profile.get("name"),
        }
