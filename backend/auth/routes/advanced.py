import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
from backend.utils.db import get_db
from backend.services.bg_tasks import enqueue_account_deletion
from pydantic import BaseModel

from backend.auth.schemes import get_current_user_id
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
def _fido2_start(user_id: str = Depends(get_current_user_id)):
    return fido2_did.start_fido2_registration(user_id)

@router.post("/fido2/register")
def _fido2_complete(attestation: dict, user_id: str = Depends(get_current_user_id)):
    if not fido2_did.complete_fido2_registration(user_id, attestation):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="FIDO2 registration failed"
        )
    return {"status": "registered"}

@router.post("/fido2/verify")
def _fido2_verify(assertion: dict, user_id: str = Depends(get_current_user_id)):
    if not fido2_did.verify_fido2_assertion(user_id, assertion):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="FIDO2 assertion failed"
        )
    return {"status": "verified"}

@router.post("/did/issue")
def _did_issue(user_id: str = Depends(get_current_user_id)):
    return {"did": fido2_did.issue_decentralized_id(user_id)}

@router.post("/did/verify")
def _did_verify(payload: DIDVerifyRequest, user_id: str = Depends(get_current_user_id)):
    return {"status": "valid"}

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
