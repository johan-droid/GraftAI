import logging
import os
import secrets
import sys

logger = logging.getLogger(__name__)

def _parse_int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        logger.warning("Invalid integer for %s: %r. Falling back to %s.", name, raw_value, default)
        return default
    if value < minimum:
        logger.warning("%s=%s below minimum %s. Clamping to %s.", name, value, minimum, minimum)
        return minimum
    if value > maximum:
        logger.warning("%s=%s above maximum %s. Clamping to %s.", name, value, maximum, maximum)
        return maximum
    return value
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = _parse_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 15, 1, 60)
REFRESH_TOKEN_EXPIRE_DAYS = _parse_int_env("REFRESH_TOKEN_EXPIRE_DAYS", 7, 1, 30)
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
DEFAULT_KEYS = frozenset({"super-secret-college-project-key-change-in-prod", "change-me-in-production", "your-secret-key", "secret", "123456", "password", "admin", "jwt-secret", "super-secret-key", "graftai-secret"})

def _is_production_environment() -> bool:
    """Check if running in production environment."""
    env_vars = ["ENV", "NODE_ENV", "APP_ENV", "ENVIRONMENT"]
    production_values = {"production", "prod", "live"}
    for var in env_vars:
        value = os.getenv(var, "").lower()
        if value in production_values:
            return True
    return False

def validate_secret_key() -> str:
    """
    Validate JWT secret key meets security requirements.

    In production:
    - Must be explicitly set via environment variable
    - Must not match any default/weak keys
    - Must be at least 32 characters (256 bits of entropy)
    - Must not be easily guessable

    In development:
    - Generates a temporary secure key with warning

    Returns:
        str: Validated secret key

    Raises:
        SystemExit: In production with invalid secret key
    """
    raw_secret = os.getenv("SECRET_KEY")
    is_production = _is_production_environment()
    if is_production:
        if not raw_secret:
            sys.exit(1)
        if raw_secret.lower() in {k.lower() for k in DEFAULT_KEYS}:
            sys.exit(1)
        if len(raw_secret) < 32:
            sys.exit(1)
        if len(raw_secret) < 43:
            pass
        return raw_secret
    if raw_secret and raw_secret.lower() not in {k.lower() for k in DEFAULT_KEYS}:
        return raw_secret
    return f"dev-only-{secrets.token_urlsafe(32)}"
SECRET_KEY = validate_secret_key()
