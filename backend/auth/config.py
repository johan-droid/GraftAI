import os
import secrets
import sys

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)  # Reduced from 1 week to 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)  # Reduced from 30 days to 7 days
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

# Default keys that must NEVER be used in production
DEFAULT_KEYS = frozenset(
    {
        "super-secret-college-project-key-change-in-prod",
        "change-me-in-production",
        "your-secret-key",
        "secret",
        "123456",
        "password",
        "admin",
        "jwt-secret",
        "super-secret-key",
        "graftai-secret",
    }
)


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

    # Production: Hard failure if secret not set or invalid
    if is_production:
        if not raw_secret:
            print("=" * 80, file=sys.stderr)
            print(
                "CRITICAL SECURITY ERROR: SECRET_KEY environment variable is not set!",
                file=sys.stderr,
            )
            print("=" * 80, file=sys.stderr)
            print(
                "\nJWT authentication is disabled without a valid SECRET_KEY.",
                file=sys.stderr,
            )
            print("\nTo fix this issue:", file=sys.stderr)
            print("1. Generate a secure key:", file=sys.stderr)
            print(
                "   python -c 'import secrets; print(secrets.token_urlsafe(32))'",
                file=sys.stderr,
            )
            print(
                "2. Set the SECRET_KEY environment variable in your production environment",
                file=sys.stderr,
            )
            print("3. Restart the application\n", file=sys.stderr)
            sys.exit(1)

        # Check against default/weak keys (case-insensitive)
        if raw_secret.lower() in {k.lower() for k in DEFAULT_KEYS}:
            print("=" * 80, file=sys.stderr)
            print(
                "CRITICAL SECURITY ERROR: SECRET_KEY is set to a default/weak value!",
                file=sys.stderr,
            )
            print("=" * 80, file=sys.stderr)
            print(
                f"\nCurrent value matches banned pattern: {raw_secret}", file=sys.stderr
            )
            print(
                "\nThis is a security risk. Generate a new secure key:", file=sys.stderr
            )
            print(
                "   python -c 'import secrets; print(secrets.token_urlsafe(32))'",
                file=sys.stderr,
            )
            sys.exit(1)

        # Check minimum entropy (at least 32 bytes = 256 bits)
        if len(raw_secret) < 32:
            print("=" * 80, file=sys.stderr)
            print("CRITICAL SECURITY ERROR: SECRET_KEY is too short!", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            print(f"\nCurrent length: {len(raw_secret)} characters", file=sys.stderr)
            print(
                "Required: Minimum 32 characters (256 bits of entropy)", file=sys.stderr
            )
            print("\nGenerate a new secure key:", file=sys.stderr)
            print(
                "   python -c 'import secrets; print(secrets.token_urlsafe(32))'",
                file=sys.stderr,
            )
            sys.exit(1)

        # Warn about short secrets (below recommended 43 chars for token_urlsafe(32))
        if len(raw_secret) < 43:
            print(
                "WARNING: SECRET_KEY is shorter than recommended 43 characters",
                file=sys.stderr,
            )
            print(
                "Consider generating a new key for enhanced security:", file=sys.stderr
            )
            print(
                "   python -c 'import secrets; print(secrets.token_urlsafe(32))'",
                file=sys.stderr,
            )

        return raw_secret

    # Development: Generate temporary key with warning
    else:
        if raw_secret and raw_secret.lower() not in {k.lower() for k in DEFAULT_KEYS}:
            # Valid custom secret provided
            return raw_secret

        # Generate development-only secret
        dev_secret = f"dev-only-{secrets.token_urlsafe(32)}"
        print("=" * 80, file=sys.stderr)
        print("WARNING: Using development-only JWT secret!", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        print(
            "\nThis secret is temporary and will change on each restart.",
            file=sys.stderr,
        )
        print(
            "Set SECRET_KEY environment variable for persistent sessions.\n",
            file=sys.stderr,
        )
        return dev_secret


# Validate and set the secret key
SECRET_KEY = validate_secret_key()
