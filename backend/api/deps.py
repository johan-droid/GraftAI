import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError

from backend.utils.db import get_db
from backend.models.tables import UserTable
from backend.services.api_keys import resolve_user_by_api_key

# This tells FastAPI where the login route is, so Swagger UI knows how to get the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-college-project-key-change-in-prod")
ALGORITHM = "HS256"

async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Helper to get just the user ID from the token or API key."""
    user = await get_current_user(token=token, db=db)
    return user.id

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
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
