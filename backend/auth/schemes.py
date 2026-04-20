from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.db import get_db
from backend.models.tables import UserTable

# We make token optional here by setting auto_error=False,
# so we can manually check cookies if the header is missing.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

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
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> str:
    user = await get_current_user(request=request, token=token, db=db)
    return user.id


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserTable:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # --- THE FIX: Fallback to checking the HttpOnly cookie ---
    if not token:
        token = request.cookies.get("graftai_access_token")

    if not token:
        raise credentials_exception
    # ---------------------------------------------------------

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

    token_version = int(payload.get("version", 0))
    if getattr(user, "token_version", 0) > token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
