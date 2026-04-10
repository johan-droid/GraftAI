from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.db import get_db
from backend.models.tables import UserTable
from backend.services.api_keys import resolve_user_by_api_key

# This tells FastAPI where the login route is, so Swagger UI knows how to get the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

from backend.auth.config import ALGORITHM, SECRET_KEY

async def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not decode token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> str:
    user = await get_current_user(token=token, db=db)
    return user.id

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
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
        api_key_user = await resolve_user_by_api_key(db, token)
        if api_key_user is not None:
            return api_key_user
        raise credentials_exception

    stmt = select(UserTable).where(UserTable.id == user_id)
    user = (await db.execute(stmt)).scalars().first()

    if user is None:
        raise credentials_exception

    return user


async def require_admin(
    current_user: UserTable = Depends(get_current_user),
) -> str:
    """Require admin privileges and return the authenticated user id."""
    is_superuser = bool(getattr(current_user, "is_superuser", False))
    is_admin_tier = getattr(current_user, "tier", None) == "admin"

    if is_superuser or is_admin_tier:
        return current_user.id

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required",
    )
