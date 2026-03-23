"""
SSO (OAuth2, OIDC) authentication implementation with fallback support.
"""
from datetime import datetime, timedelta
import os
import uuid
from fastapi import HTTPException
from authlib.integrations.requests_client import OAuth2Session

# In-memory state manager for demonstration purposes
_oauth_state_cache: dict[str, dict] = {}

# Multi-provider configuration
PROVIDERS = {
    "github": {
        "client_id": os.getenv("GITHUB_CLIENT_ID") or os.getenv("OAUTH2_CLIENT_ID"),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET") or os.getenv("OAUTH2_CLIENT_SECRET"),
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scope": "read:user user:email",
    },
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scope": "openid profile email",
    },
}

OAUTH2_REDIRECT_URI = os.getenv("OAUTH2_REDIRECT_URI", "http://localhost:8000/auth/sso/callback")


def start_oauth2_flow(provider: str = "github", redirect_to: str = "/dashboard"):
    config = PROVIDERS.get(provider.lower())
    if not config:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not supported")

    client_id = config["client_id"]
    client_secret = config["client_secret"]

    if not all([client_id, client_secret]):
        raise RuntimeError(f"OAuth2 credentials for {provider} are not configured")

    session = OAuth2Session(
        client_id=client_id,
        client_secret=client_secret,
        scope=config["scope"],
        redirect_uri=OAUTH2_REDIRECT_URI,
    )

    authorization_url, state = session.create_authorization_url(config["auth_url"])
    _oauth_state_cache[state] = {
        "created_at": datetime.utcnow(),
        "session": session,
        "redirect_to": redirect_to,
        "provider": provider.lower(),
    }

    return {
        "authorization_url": authorization_url,
        "state": state,
        "expires_in_seconds": 300,
        "redirect_to": redirect_to,
        "provider": provider,
    }


def complete_oauth2_flow(code: str, state: str):
    data = _oauth_state_cache.pop(state, None)
    if not data:
        raise RuntimeError("Invalid or expired state")

    if datetime.utcnow() - data["created_at"] > timedelta(minutes=5):
        raise RuntimeError("OAuth2 state expired")

    provider_name = data.get("provider", "github")
    config = PROVIDERS.get(provider_name)
    session: OAuth2Session = data["session"]

    token = session.fetch_token(
        config["token_url"],
        code=code,
        include_client_id=True,
        client_secret=config["client_secret"],
        authorization_response=f"?code={code}&state={state}",
    )

    import httpx

    headers = {"Authorization": f"Bearer {token.get('access_token')}"}
    userinfo_resp = httpx.get(config["userinfo_url"], headers=headers)
    userinfo_resp.raise_for_status()

    profile = userinfo_resp.json()

    redirect_to = data.get("redirect_to", "/dashboard")

    # Normalize user profile across providers
    user_id = profile.get("id") or profile.get("sub")
    name = profile.get("name") or profile.get("login") or profile.get("given_name")
    email = profile.get("email")

    return {
        "provider": provider_name,
        "profile": {
            "id": user_id,
            "name": name,
            "email": email,
        },
        "token": token,
        "redirect_to": redirect_to,
    }

