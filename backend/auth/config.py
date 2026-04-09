import os

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-college-project-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week token
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

# Security: Validate that SECRET_KEY is set in production
if os.getenv("ENV") == "production" and SECRET_KEY == "super-secret-college-project-key-change-in-prod":
    raise ValueError(
        "CRITICAL SECURITY ERROR: SECRET_KEY must be changed in production! "
        "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )
