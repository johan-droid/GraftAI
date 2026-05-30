import os
from pathlib import Path

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parents[1]
for dotenv_file in [".env", ".env.local", ".env.development", ".env.development.local"]:
    path = backend_dir / dotenv_file
    if path.exists():
        load_dotenv(dotenv_path=path, override=False)
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID") or os.getenv("MICROSOFT_ID") or os.getenv("AUTH_MICROSOFT_ENTRA_ID_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET") or os.getenv("MICROSOFT_SECRET") or os.getenv("AUTH_MICROSOFT_ENTRA_ID_SECRET")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI", f"{BACKEND_URL}/api/v1/auth/microsoft/callback")
if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
    import logging
    logging.warning("⚠️  Microsoft OAuth not fully configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET or AUTH_MICROSOFT_ENTRA_ID_ID and AUTH_MICROSOFT_ENTRA_ID_SECRET to enable Microsoft login. Visit https://portal.azure.com to create app registrations.")
AUTHORITY = "https://login.microsoftonline.com/common"
AUTH_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/authorize"
TOKEN_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/token"
SCOPES = "openid profile email offline_access Calendars.ReadWrite"
HTTP_TIMEOUT = httpx.Timeout(10.0, connect=5.0)

async def get_microsoft_auth_url(state: str):
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        msg = "Microsoft OAuth is not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET or AUTH_MICROSOFT_ENTRA_ID_ID and AUTH_MICROSOFT_ENTRA_ID_SECRET in your .env file. Get credentials from: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
        raise ValueError(msg)
    client = AsyncOAuth2Client(client_id=MICROSOFT_CLIENT_ID, client_secret=MICROSOFT_CLIENT_SECRET, scope=SCOPES, redirect_uri=MICROSOFT_REDIRECT_URI)
    authorization_url, _ = client.create_authorization_url(AUTH_ENDPOINT, state=state, response_mode="query")
    return authorization_url

async def fetch_microsoft_tokens(code: str):
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        msg = "Microsoft OAuth is not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET in your .env file. Get credentials from: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
        raise ValueError(msg)
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        msg = "Microsoft OAuth is not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET or AUTH_MICROSOFT_ENTRA_ID_ID and AUTH_MICROSOFT_ENTRA_ID_SECRET in your .env file. Get credentials from: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
        raise ValueError(msg)
    async with AsyncOAuth2Client(client_id=MICROSOFT_CLIENT_ID, client_secret=MICROSOFT_CLIENT_SECRET, timeout=HTTP_TIMEOUT) as client:
        token = await client.fetch_token(TOKEN_ENDPOINT, code=code, grant_type="authorization_code", redirect_uri=MICROSOFT_REDIRECT_URI)
        resp = await client.get("https://graph.microsoft.com/v1.0/me")
        resp.raise_for_status()
        profile = resp.json()
    return {"email": profile.get("mail") or profile.get("userPrincipalName"), "full_name": profile.get("displayName"), "token": token}

async def verify_microsoft_token(access_token: str) -> dict:
    if not access_token:
        msg = "No access token provided"
        raise ValueError(msg)
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get("https://graph.microsoft.com/v1.0/me", headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"})
            if resp.status_code != 200:
                msg = "Invalid Microsoft access token"
                raise ValueError(msg)
            profile = resp.json()
            return {"email": profile.get("mail") or profile.get("userPrincipalName"), "full_name": profile.get("displayName")}
    except httpx.TimeoutException as exc:
        msg = "Microsoft token verification timed out"
        raise ValueError(msg) from exc
    except httpx.HTTPError as exc:
        msg = "Microsoft token verification failed"
        raise ValueError(msg) from exc
