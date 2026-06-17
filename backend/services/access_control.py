from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import UserTable
from backend.utils.logger import get_logger

logger = get_logger(__name__)

async def check_user_role(db: AsyncSession, user_id: str, role: str) -> bool:
    """
    Checks if a user has a specific role.
    Roles are stored in user.preferences['role'] since the dedicated column was removed.
    'admin' role is granted to users with tier='elite' as a fallback.
    """
    user = await db.get(UserTable, user_id)
    if not user:
        return False
    prefs = user.preferences or {}
    user_role = prefs.get("role", "member") if isinstance(prefs, dict) else "member"
    if role == "admin" and user.tier in ("elite", "admin"):
        return True
    return user_role == role

async def get_user_role(db: AsyncSession, user_id: str) -> str:
    """Retrieves the primary role of a user from preferences."""
    user = await db.get(UserTable, user_id)
    if not user:
        return "member"
    prefs = user.preferences or {}
    if isinstance(prefs, dict):
        return prefs.get("role", "member")
    return "member"
ALLOWED_ATTRIBUTES = {"tier", "subscription_status", "role", "timezone", "onboarding_completed"}

async def check_user_attribute(db: AsyncSession, user_id: str, attribute: str, value: str) -> bool:
    """
    Checks whether a user attribute matches the requested value.

    SECURITY: Only whitelisted attributes can be checked to prevent
    information disclosure (e.g., password_hash, mfa_secret).
    """
    if attribute not in ALLOWED_ATTRIBUTES:
        logger.warning(" Blocked check_user_attribute attempt for non-whitelisted attribute: %s", attribute)
        return False
    user = await db.get(UserTable, user_id)
    if not user:
        return False
    attr_value = getattr(user, attribute, None)
    if attr_value is None:
        prefs = user.preferences or {}
        if isinstance(prefs, dict):
            attr_value = prefs.get(attribute)
    if attr_value is None:
        return False
    return str(attr_value).lower() == str(value).lower()
