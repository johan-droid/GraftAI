from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from backend.services.auth_service import decode_jwt_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import UserTable
from backend.utils.db import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
from backend.auth.config import ALGORITHM, SECRET_KEY


async def decode_token(token: str) -> dict:
    try:
        return await decode_jwt_token(token)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not decode token", headers={"WWW-Authenticate": "Bearer"}) from exc

async def get_current_user_id(request: Request, token: str=Depends(oauth2_scheme), db: AsyncSession=Depends(get_db)) -> str:
    user = await get_current_user(request=request, token=token, db=db)
    return user.id

async def get_current_user(request: Request, token: str=Depends(oauth2_scheme), db: AsyncSession=Depends(get_db)) -> UserTable:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    if not token:
        token = request.cookies.get("graftai_access_token")
    if not token:
        raise credentials_exception
    try:
        payload = await decode_jwt_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except HTTPException:
        raise credentials_exception
    stmt = select(UserTable).where(UserTable.id == user_id)
    user = (await db.execute(stmt)).scalars().first()
    if user is None:
        raise credentials_exception
    token_version = int(payload.get("version", 0))
    if getattr(user, "token_version", 0) > token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been revoked. Please log in again.", headers={"WWW-Authenticate": "Bearer"})
    return user

async def require_admin(current_user: UserTable=Depends(get_current_user)) -> str:
    """Require admin privileges and return the authenticated user id."""
    is_superuser = bool(getattr(current_user, "is_superuser", False))
    is_admin_tier = getattr(current_user, "tier", None) == "admin"
    if is_superuser or is_admin_tier:
        return current_user.id
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
