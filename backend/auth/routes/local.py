import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.api.deps import get_db
from backend.services import auth_utils
from backend.models.tables import UserTable
from backend.auth.logic import (
    get_rate_limiter,
    create_jwt_token,
    attach_jwt_cookies
)

logger = logging.getLogger(__name__)
router = APIRouter()

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    timezone: Optional[str] = None

@router.post("/token")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=5, window_seconds=60)),
):
    email = auth_utils.canonical_email(form_data.username)
    result = await db.execute(select(UserTable).where(UserTable.email == email))
    user = result.scalars().first()

    dummy_hash = auth_utils.get_password_hash("dummy-constant-string")
    stored_hash = user.hashed_password if (user and user.hashed_password) else dummy_hash
    password_ok = auth_utils.verify_password(form_data.password, stored_hash)

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    tokens = create_jwt_token(str(user.id), email=user.email)
    response = JSONResponse(
        content={
            "message": "Login successful",
            "user": {"id": user.id, "email": user.email},
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
        }
    )
    attach_jwt_cookies(response, tokens, request)
    return response

@router.post("/register")
async def register(
    user_in: UserRegister,
    db: AsyncSession = Depends(get_db),
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=3, window_seconds=60)),
):
    email = auth_utils.canonical_email(user_in.email)
    if not auth_utils.validate_password_complexity(user_in.password):
        raise HTTPException(
            status_code=400,
            detail="Password does not meet complexity requirements (12+ chars, mixed cases, digits, symbols)",
        )

    try:
        async with db.begin():
            result = await db.execute(select(UserTable).where(UserTable.email == email))
            if result.scalars().first():
                logger.warning(f"Registration attempt for existing email: {email}")
                raise HTTPException(
                    status_code=400,
                    detail="Registration failed. Please try a different email or login.",
                )

            new_user = UserTable(
                id=str(uuid.uuid4()),
                email=email,
                full_name=user_in.full_name,
                hashed_password=auth_utils.get_password_hash(user_in.password),
                timezone=user_in.timezone or "UTC",
                is_active=True,
                is_superuser=False,
                tier="free",
                subscription_status="inactive",
                daily_ai_count=0,
                daily_sync_count=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                consent_analytics=True,
                consent_notifications=True,
                consent_ai_training=False,
            )
            db.add(new_user)
            await db.flush()

        try:
            from backend.services.bg_tasks import enqueue_welcome_email
            await enqueue_welcome_email(
                user_email=email,
                full_name=user_in.full_name or email.split("@")[0],
            )
        except Exception as e:
            logger.warning(f"Failed to enqueue welcome email in register: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Registration failed")
        raise HTTPException(status_code=500, detail="Registration failed")

    return {"message": "User registered successfully", "id": new_user.id}
