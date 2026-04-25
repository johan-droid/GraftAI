import os
from fastapi import HTTPException
from starlette import status

PROVIDERS = {
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID")
        or os.getenv("GOOGLE_ID")
        or os.getenv("AUTH_GOOGLE_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET")
        or os.getenv("GOOGLE_SECRET")
        or os.getenv("AUTH_GOOGLE_SECRET"),
        "token_url": "https://oauth2.googleapis.com/token",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
    },
    "microsoft": {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    },
    "zoom": {
        "client_id": os.getenv("ZOOM_CLIENT_ID"),
        "client_secret": os.getenv("ZOOM_CLIENT_SECRET"),
        "token_url": "https://zoom.us/oauth/token",
        "auth_url": "https://zoom.us/oauth/authorize",
    },
}


def get_provider_config(provider: str):
    """
    Returns the OAuth2 configuration for the specified provider.
    In the monolithic GraftAI, this reads directly from environment variables.
    """
    return PROVIDERS.get(provider)


def start_oauth2_flow(provider: str, redirect_path: str):
    config = get_provider_config(provider)
    if not config or not config.get("client_id") or not config.get("client_secret"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{provider} is currently unavailable",
        )
    # Return the provider auth URL for integration readiness checks.
    return config["auth_url"]
