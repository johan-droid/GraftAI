import os
from authlib.integrations.httpx_client import AsyncOAuth2Client

MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8000/api/v1/auth/microsoft/callback")

# Validate Microsoft OAuth configuration
if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
    import logging
    logging.warning(
        "⚠️  Microsoft OAuth not fully configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET to enable Microsoft login. "
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
            "Microsoft OAuth is not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET in your .env file. "
            "Get credentials from: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
        )
    
    client = AsyncOAuth2Client(
        client_id=MICROSOFT_CLIENT_ID,
        client_secret=MICROSOFT_CLIENT_SECRET,
        scope=SCOPES,
        redirect_uri=MICROSOFT_REDIRECT_URI,
    )
    authorization_url, _ = client.create_authorization_url(
        AUTH_ENDPOINT,
        state=state,
        response_mode="query"
    )
    return authorization_url

async def fetch_microsoft_tokens(code: str):
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        raise ValueError(
            "Microsoft OAuth is not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET in your .env file. "
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
        "token": token
    }
