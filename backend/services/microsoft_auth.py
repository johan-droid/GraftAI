import os
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

MICROSOFT_CLIENT_ID = (
    os.getenv("MICROSOFT_CLIENT_ID")
    or os.getenv("MICROSOFT_ID")
    or os.getenv("AUTH_MICROSOFT_ENTRA_ID_ID")
)
MICROSOFT_CLIENT_SECRET = (
    os.getenv("MICROSOFT_CLIENT_SECRET")
    or os.getenv("MICROSOFT_SECRET")
    or os.getenv("AUTH_MICROSOFT_ENTRA_ID_SECRET")
)

# Use the backend base URL provided through environment variables.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
MICROSOFT_REDIRECT_URI = os.getenv(
    "MICROSOFT_REDIRECT_URI", f"{BACKEND_URL}/api/v1/auth/microsoft/callback"
)

# Validate Microsoft OAuth configuration
if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
    import logging

    logging.warning(
        "⚠️  Microsoft OAuth not fully configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET "
        "or AUTH_MICROSOFT_ENTRA_ID_ID and AUTH_MICROSOFT_ENTRA_ID_SECRET to enable Microsoft login. "
        "Visit https://portal.azure.com to create app registrations."
    )

# Common tenant for multi-tenant apps
AUTHORITY = "https://login.microsoftonline.com/common"
AUTH_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/authorize"
TOKEN_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/token"

# Scopes for Graph Calendar access
SCOPES = "openid profile email offline_access Calendars.ReadWrite"


async def get_microsoft_auth_url(state: str):
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        raise ValueError(
            "Microsoft OAuth is not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET "
            "or AUTH_MICROSOFT_ENTRA_ID_ID and AUTH_MICROSOFT_ENTRA_ID_SECRET in your .env file. "
            "Get credentials from: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
        )

    client = AsyncOAuth2Client(
        client_id=MICROSOFT_CLIENT_ID,
        client_secret=MICROSOFT_CLIENT_SECRET,
        scope=SCOPES,
        redirect_uri=MICROSOFT_REDIRECT_URI,
    )
    authorization_url, _ = client.create_authorization_url(
        AUTH_ENDPOINT, state=state, response_mode="query"
    )
    return authorization_url


async def fetch_microsoft_tokens(code: str):
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        raise ValueError(
            "Microsoft OAuth is not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET in your .env file. "
            "Get credentials from: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
        )

    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        raise ValueError(
            "Microsoft OAuth is not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET "
            "or AUTH_MICROSOFT_ENTRA_ID_ID and AUTH_MICROSOFT_ENTRA_ID_SECRET in your .env file. "
            "Get credentials from: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
        )

    async with AsyncOAuth2Client(
        client_id=MICROSOFT_CLIENT_ID,
        client_secret=MICROSOFT_CLIENT_SECRET,
    ) as client:
        token = await client.fetch_token(
            TOKEN_ENDPOINT,
            code=code,
            grant_type="authorization_code",
            redirect_uri=MICROSOFT_REDIRECT_URI,
        )
        # Fetch profile from Graph /me
        resp = await client.get("https://graph.microsoft.com/v1.0/me")
        profile = resp.json()
    return {
        "email": profile.get("mail") or profile.get("userPrincipalName"),
        "full_name": profile.get("displayName"),
        "token": token,
    }


async def verify_microsoft_token(access_token: str) -> dict:
    if not access_token:
        raise ValueError("No access token provided")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        if resp.status_code != 200:
            raise ValueError("Invalid Microsoft access token")
        profile = resp.json()
        return {
            "email": profile.get("mail") or profile.get("userPrincipalName"),
            "full_name": profile.get("displayName"),
        }
