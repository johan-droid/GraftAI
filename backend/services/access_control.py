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
