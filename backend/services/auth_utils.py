import logging
from passlib.context import CryptContext

# Initialize logger
logger = logging.getLogger(__name__)

# Use standard bcrypt scheme for better compatibility.
# For Python 3.12+ / passlib 1.7.x compatibility, ensure 'bcrypt' package is installed.
# We validate immediately at import time to fail fast in case the backend is incompatible.

def _init_pwd_context() -> CryptContext:
    try:
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # quick self-test to catch bcrypt backend load problems early
        ctx.hash("StartupSelfTest99!")
        return ctx
    except Exception as e:
        logger.critical(
            "Missing or incompatible bcrypt backend. "
            "Please install bcrypt<4 and passlib>=1.7.4. "
            f"Underlying error: {type(e).__name__}: {e}"
        )
        raise

pwd_context = _init_pwd_context()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification failed: {type(e).__name__}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt. 
    Note: Standard Bcrypt has a 72-character limit; any characters beyond this are ignored. 
    We enforce this limit at the application level to be explicit and secure.
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    try:
        # Bcrypt limit is 72 bytes. We check UTF-8 length.
        if len(password.encode("utf-8")) > 72:
            logger.warning("Password hashing rejected: length exceeds bcrypt limit (72 bytes)")
            raise ValueError("Password is too long (max 72 characters for security)")
            
        return pwd_context.hash(password)
    except ValueError:
        raise
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
