import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
from backend.utils.db import get_db
from backend.services.bg_tasks import enqueue_account_deletion
from pydantic import BaseModel, EmailStr

from backend.auth.schemes import get_current_user_id, get_current_user_id_optional
from backend.models.tables import UserTable
from backend.services import passwordless, fido2_did, access_control
from backend.auth.logic import (
    get_rate_limiter,
    create_jwt_token,
    attach_jwt_cookies
)

logger = logging.getLogger(__name__)
router = APIRouter()

class DIDVerifyRequest(BaseModel):
    did: str

@router.post("/passwordless/request")
def _passwordless_request(
    email: str,
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=3, window_seconds=300)),
):
    return passwordless.request_magic_link(email)

@router.post("/passwordless/verify")
async def _passwordless_verify(
    request: Request,
    email: str,
    code: str,
    _rate_limit: bool = Depends(get_rate_limiter(max_requests=5, window_seconds=60)),
):
    if not passwordless.verify_magic_link_code(email, code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP"
        )
    token_data = await create_jwt_token(email)
    response = JSONResponse(content=token_data)
    attach_jwt_cookies(response, token_data, request)
    return response

# MFA is handled by the dedicated backend.api.mfa router.
# FIDO2 below


@router.get("/fido2/register")
async def _fido2_start(user_id: str = Depends(get_current_user_id)):
    return await fido2_did.start_fido2_registration(user_id)

@router.post("/fido2/register")
async def _fido2_complete(attestation: dict, user_id: str = Depends(get_current_user_id)):
    if not await fido2_did.complete_fido2_registration(user_id, attestation):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="FIDO2 registration failed"
        )
    return {"status": "registered"}

class Fido2AssertionRequest(BaseModel):
    email: EmailStr
    assertion: dict

@router.post("/fido2/verify")
def _fido2_verify(assertion: dict, user_id: str = Depends(get_current_user_id)):
    if not fido2_did.verify_fido2_assertion(user_id, assertion):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="FIDO2 assertion failed"
        )
    return {"status": "verified"}

@router.get("/fido2/register/start")
async def _fido2_register_start(
    email: Optional[EmailStr] = None,
    current_user_id: Optional[str] = Depends(get_current_user_id_optional),
    db: AsyncSession = Depends(get_db),
):
    if not email and not current_user_id:
        raise HTTPException(status_code=400, detail="Email or authenticated user required")

    if email:
        result = await db.execute(select(UserTable).where(UserTable.email == email))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = str(user.id)
    else:
        user_id = current_user_id

    data = await fido2_did.start_fido2_registration(user_id)
    if not data:
        raise HTTPException(status_code=500, detail="Unable to initialize passkey registration")
    return data

@router.post("/fido2/register/complete")
async def _fido2_register_complete(
    email: Optional[EmailStr] = None,
    attestation: dict = None,
    current_user_id: Optional[str] = Depends(get_current_user_id_optional),
    db: AsyncSession = Depends(get_db),
):
    if not attestation:
        raise HTTPException(status_code=400, detail="Attestation payload is required")

    if not email and not current_user_id:
        raise HTTPException(status_code=400, detail="Email or authenticated user required")

    if email:
        result = await db.execute(select(UserTable).where(UserTable.email == email))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = str(user.id)
    else:
        user_id = current_user_id

    if not await fido2_did.complete_fido2_registration(user_id, attestation):
        raise HTTPException(status_code=400, detail="FIDO2 registration failed")

    return {"status": "registered"}

@router.get("/fido2/login/start")
async def _fido2_login_start(email: EmailStr, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserTable).where(UserTable.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = await fido2_did.start_fido2_authentication(str(user.id))
    if not data:
        raise HTTPException(status_code=404, detail="No passkey registered for this account")
    return data

@router.post("/fido2/login/complete")
async def _fido2_login_complete(
    payload: Fido2AssertionRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserTable).where(UserTable.email == payload.email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not await fido2_did.verify_fido2_assertion(str(user.id), payload.assertion):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="FIDO2 assertion failed")

    token_data = await create_jwt_token(str(user.id), email=user.email)
    response = JSONResponse(content={"message": "Login successful", "access_token": token_data["access_token"], "refresh_token": token_data["refresh_token"], "token_type": token_data["token_type"], "expires_in": token_data["expires_in"]})
    attach_jwt_cookies(response, token_data)
    return response

@router.post("/did/issue")
async def _did_issue(user_id: str = Depends(get_current_user_id)):
    return {"did": await fido2_did.issue_decentralized_id(user_id)}

@router.post("/did/verify")
async def _did_verify(payload: DIDVerifyRequest, user_id: str = Depends(get_current_user_id)):
    valid = await fido2_did.verify_decentralized_id(user_id, payload.did)
    return {"status": "valid" if valid else "invalid"}

@router.get("/access-control/check-role")
async def check_role(
    role: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return {"allowed": await access_control.check_user_role(db, user_id, role)}

@router.get("/access-control/check-attribute")
async def check_attribute(
    attribute: str,
    value: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return {"allowed": await access_control.check_user_attribute(db, user_id, attribute, value)}

@router.delete("/account")
async def delete_account(
    response: Response,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Business-grade account deletion lifecycle.
    Triggers 'Goodbye' email and purges user data.
    """
    from backend.models.tables import UserTable
    
    user = await db.get(UserTable, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 1. Trigger professional 'Goodbye' email
    if user.email:
        await enqueue_account_deletion(user.email)
        logger.info(f"📧 Goodbye email enqueued for user {user.email}")
    else:
        logger.warning(f"Goodbye email skipped because user {user_id} has no email address")
    
    # 2. Soft-Delete (30-day Retention Policy)
    # Audit: Set deleted_at timestamp and deactivate account immediately.
    from datetime import datetime, timezone
    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False
    
    await db.commit()
    logger.info(f"🔒 Account soft-deleted for user {user.email}")
    
    # 3. Revoke Session Cookies Immediately
    response.delete_cookie(key="better-auth.session_token", path="/")
    response.delete_cookie(key="graftai_access_token", path="/")
    
    return {
        "status": "account_deactivated", 
        "message": "Your account has been deactivated. All data will be permanently purged in 30 days."
    }
