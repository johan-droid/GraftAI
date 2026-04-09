import os

def get_provider_config(provider: str):
    """
    Returns the OAuth2 configuration for the specified provider.
    In the monolithic GraftAI, this reads directly from environment variables.
    """
    if provider == "google":
        return {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "token_url": "https://oauth2.googleapis.com/token",
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        }
    elif provider == "microsoft":
        return {
            "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
            "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        }
    elif provider == "zoom":
        return {
            "client_id": os.getenv("ZOOM_CLIENT_ID"),
            "client_secret": os.getenv("ZOOM_CLIENT_SECRET"),
            "token_url": "https://zoom.us/oauth/token",
            "auth_url": "https://zoom.us/oauth/authorize",
        }
    return None
