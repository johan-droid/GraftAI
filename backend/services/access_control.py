from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.tables import UserTable


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
    if isinstance(prefs, dict):
        user_role = prefs.get("role", "member")
    else:
        user_role = "member"

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


async def check_user_attribute(
    db: AsyncSession, user_id: str, attribute: str, value: str
) -> bool:
    """Checks whether a user attribute matches the requested value."""
    user = await db.get(UserTable, user_id)
    if not user:
        return False

    attr_value = getattr(user, attribute, None)
    if attr_value is None:
        # Fall back to preferences dict for removed columns
        prefs = user.preferences or {}
        if isinstance(prefs, dict):
            attr_value = prefs.get(attribute)
    if attr_value is None:
        return False
    return str(attr_value).lower() == str(value).lower()
