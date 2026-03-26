import logging
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Initialize logger
logger = logging.getLogger(__name__)

# Argon2 is the winner of the Password Hashing Competition (PHC) and is recommended by OWASP/NIST.
ph = PasswordHasher(
    time_cost=3,  # Number of iterations
    memory_cost=65536,  # 64MB memory usage
    parallelism=4,  # Number of threads
    hash_len=32,  # Length of the hash
    salt_len=16,  # Length of the salt
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against an Argon2 hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except Exception as e:
        logger.error(f"Password verification failed: {type(e).__name__}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using Argon2.
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    try:
        return ph.hash(password)
    except Exception as e:
        logger.error(f"Password hashing failed: {type(e).__name__}")
        raise RuntimeError("Internal authentication error")


def canonical_email(email: str) -> str:
    """Normalize email for consistent lookup and to prevent enumeration/bypass."""
    if not email:
        return ""
    return email.strip().lower()


def validate_password_complexity(password: str) -> bool:
    """Check for enterprise-grade password complexity: 12+ chars, mixed cases, digits, symbols."""
    # Length check (NIST/OWASP recommendation: 12+)
    if len(password) < 12:
        return False

    import re

    # Check for lowercase
    if not re.search(r"[a-z]", password):
        return False
    # Check for uppercase
    if not re.search(r"[A-Z]", password):
        return False
    # Check for numbers
    if not re.search(r"\d", password):
        return False
    # Check for special characters
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False

    return True
