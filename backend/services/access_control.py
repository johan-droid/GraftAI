from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.tables import UserTable

async def check_user_role(db: AsyncSession, user_id: str, role: str) -> bool:
    """
    Checks if a user has a specific role using the database.
    Source of truth for Phase 1 RBAC.
    """
    user = await db.get(UserTable, user_id)
    if not user:
        return False
    
    # Superusers always have admin access
    if user.is_superuser:
        return True
        
    return user.role == role

async def get_user_role(db: AsyncSession, user_id: str) -> str:
    """Retrieves the primary role of a user."""
    user = await db.get(UserTable, user_id)
    return user.role if user else "member"

async def check_user_attribute(
    db: AsyncSession, user_id: str, attribute: str, value: str
) -> bool:
    """Checks whether a user attribute matches the requested value."""
    user = await db.get(UserTable, user_id)
    if not user:
        return False

    attr_value = getattr(user, attribute, None)
    if attr_value is None:
        return False
    return str(attr_value).lower() == str(value).lower()
