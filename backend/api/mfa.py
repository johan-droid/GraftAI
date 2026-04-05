from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_db
from backend.auth.schemes import get_current_user_id
from backend.services.mfa import start_mfa_enrollment, verify_mfa_token, enable_mfa
from pydantic import BaseModel

router = APIRouter(prefix="/auth/mfa", tags=["mfa"])

class MFASetupResponse(BaseModel):
    secret: str
    otp_uri: str

class MFAVerifyRequest(BaseModel):
    token: str
    secret: str # Temporary secret from setup

@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Initiates MFA enrollment for the current user."""
    return await start_mfa_enrollment(db, user_id)

@router.post("/verify")
async def verify_and_enable_mfa(
    req: MFAVerifyRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Verifies the first token and formally enables MFA."""
    is_valid = await verify_mfa_token(db, user_id, req.token, temp_secret=req.secret)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA token"
        )
    
    success = await enable_mfa(db, user_id, req.secret)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to enable MFA")
        
    return {"status": "success", "message": "MFA enabled successfully"}

@router.get("/status")
async def get_mfa_status(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Checks if MFA is currently enabled for the user."""
    from backend.models.tables import UserTable
    user = await db.get(UserTable, user_id)
    return {"enabled": user.mfa_enabled if user else False}
