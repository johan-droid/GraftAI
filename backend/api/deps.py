from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError

from backend.utils.db import get_db
from backend.models.tables import UserTable

# This tells FastAPI where the login route is, so Swagger UI knows how to get the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/social/exchange")

from backend.auth.config import SECRET_KEY, ALGORITHM


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Helper to get just the user ID from the token or API key."""
    user = await get_current_user(token=token, db=db)
    return user.id


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> UserTable:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(UserTable).where(UserTable.id == user_id)
    user = (await db.execute(stmt)).scalars().first()

    if user is None:
        raise credentials_exception

    raw_version = payload.get("version", 0)
    try:
        token_version = int(raw_version)
    except (ValueError, TypeError):
        token_version = 0
    if getattr(user, "token_version", 0) > token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def require_active_subscription(
    current_user: UserTable = Depends(get_current_user),
) -> UserTable:
    """Dependency to enforce active paid subscription or active trial for premium endpoints."""
    # Fields are non-nullable with defaults on the model, so access directly
    if current_user.subscription_status == "active":
        return current_user
    if current_user.trial_active:
        return current_user
    # 402 Payment Required is appropriate for subscription gating
    raise HTTPException(
        status_code=402, detail="Active subscription required to access this resource"
    )
