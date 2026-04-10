"""Multi-Factor Authentication (MFA) implementation using TOTP."""

import base64
import hashlib
import hmac
import io
import logging
import secrets
from datetime import datetime, timezone
from typing import List

import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.schemes import get_current_user_id
from backend.models.tables import UserMFATable, UserTable
from backend.utils.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Multi-Factor Authentication"])

# Encryption key for TOTP secrets - MUST be set in environment for production
import os
TOTP_ENCRYPTION_KEY = os.getenv("TOTP_ENCRYPTION_KEY", "").encode() if os.getenv("TOTP_ENCRYPTION_KEY") else secrets.token_bytes(32)
if os.getenv("ENV", "development").lower() == "production" and not os.getenv("TOTP_ENCRYPTION_KEY"):
    raise RuntimeError("TOTP_ENCRYPTION_KEY must be set in production environment")


class MFASetupResponse(BaseModel):
    """Response for MFA setup initiation."""
    secret: str
    qr_code_uri: str
    qr_code_image: str  # Base64 encoded PNG
    backup_codes: List[str]


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA setup."""
    code: str


class MFAVerifyResponse(BaseModel):
    """Response after MFA verification."""
    message: str
    enabled: bool


class MFALoginRequest(BaseModel):
    """Request for MFA verification during login."""
    temp_token: str
    code: str


class MFADisableRequest(BaseModel):
    """Request to disable MFA."""
    password: str
    code: str  # Current TOTP code for verification


def _encrypt_secret(secret: str) -> str:
    """Encrypt TOTP secret before storage using Fernet encryption."""
    from cryptography.fernet import Fernet
    import hashlib
    
    # Derive Fernet key from TOTP_ENCRYPTION_KEY
    key = hashlib.sha256(TOTP_ENCRYPTION_KEY).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    fernet = Fernet(fernet_key)
    
    encrypted = fernet.encrypt(secret.encode())
    return encrypted.decode()


def _decrypt_secret(encrypted: str) -> str:
    """Decrypt TOTP secret for verification using Fernet encryption."""
    from cryptography.fernet import Fernet
    import hashlib
    
    # Derive Fernet key from TOTP_ENCRYPTION_KEY
    key = hashlib.sha256(TOTP_ENCRYPTION_KEY).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    fernet = Fernet(fernet_key)
    
    decrypted = fernet.decrypt(encrypted.encode())
    return decrypted.decode()


def _hash_backup_code(code: str) -> str:
    """Hash backup code for secure storage."""
    return hashlib.sha256(code.encode()).hexdigest()


def _verify_backup_code(code: str, hashed: str) -> bool:
    """Verify a backup code against its hash."""
    return hmac.compare_digest(_hash_backup_code(code), hashed)


def _generate_backup_codes(count: int = 10) -> List[str]:
    """Generate one-time backup codes."""
    return [secrets.token_hex(4) for _ in range(count)]


@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Initialize MFA setup for user.
    
    Generates TOTP secret and QR code for authenticator app setup.
    Returns backup codes that should be saved securely by the user.
    """
    # Check if MFA already enabled
    stmt = select(UserMFATable).where(
        UserMFATable.user_id == user_id,
        UserMFATable.is_enabled == True
    )
    existing = (await db.execute(stmt)).scalars().first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled for this account"
        )
    
    # Generate TOTP secret
    totp_secret = pyotp.random_base32()
    
    # Get user email for provisioning URI
    user_stmt = select(UserTable).where(UserTable.id == user_id)
    user = (await db.execute(user_stmt)).scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create provisioning URI for authenticator apps
    totp = pyotp.TOTP(totp_secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name="GraftAI"
    )
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    # Generate backup codes
    backup_codes = _generate_backup_codes(10)
    hashed_backup_codes = [_hash_backup_code(code) for code in backup_codes]
    
    # Create or update MFA record (pending verification)
    mfa_stmt = select(UserMFATable).where(UserMFATable.user_id == user_id)
    mfa_record = (await db.execute(mfa_stmt)).scalars().first()
    
    if mfa_record:
        # Update existing pending record
        mfa_record.secret = _encrypt_secret(totp_secret)
        mfa_record.backup_codes = hashed_backup_codes
        mfa_record.is_enabled = False
        mfa_record.verified_at = None
    else:
        # Create new record
        mfa_record = UserMFATable(
            user_id=user_id,
            mfa_type="totp",
            secret=_encrypt_secret(totp_secret),
            backup_codes=hashed_backup_codes,
            is_enabled=False,
        )
        db.add(mfa_record)
    
    await db.commit()
    
    logger.info(f"MFA setup initiated for user: {user.email}")
    
    return MFASetupResponse(
        secret=totp_secret,  # Only shown once during setup
        qr_code_uri=provisioning_uri,
        qr_code_image=f"data:image/png;base64,{qr_base64}",
        backup_codes=backup_codes,  # Only shown once
    )


@router.post("/verify-setup", response_model=MFAVerifyResponse)
async def verify_mfa_setup(
    request: MFAVerifyRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify MFA setup with initial TOTP code.
    
    Enables MFA after successful verification of the setup code.
    """
    # Get pending MFA record
    stmt = select(UserMFATable).where(
        UserMFATable.user_id == user_id,
        UserMFATable.is_enabled == False
    )
    mfa_record = (await db.execute(stmt)).scalars().first()
    
    if not mfa_record or not mfa_record.secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup not initiated. Call /setup first."
        )
    
    # Verify TOTP code
    try:
        secret = _decrypt_secret(mfa_record.secret)
        totp = pyotp.TOTP(secret)
        
        # Allow 1 time step before/after for clock skew
        if not totp.verify(request.code, valid_window=1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code. Please try again."
            )
    except Exception as e:
        logger.error(f"MFA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify MFA code"
        )
    
    # Enable MFA
    mfa_record.is_enabled = True
    mfa_record.verified_at = datetime.now(timezone.utc)
    await db.commit()
    
    # Get user for logging
    user_stmt = select(UserTable).where(UserTable.id == user_id)
    user = (await db.execute(user_stmt)).scalars().first()
    
    logger.info(f"MFA enabled for user: {user.email}")
    
    return MFAVerifyResponse(
        message="MFA enabled successfully. Please save your backup codes securely.",
        enabled=True
    )


@router.post("/verify")
async def verify_mfa_login(
    request: MFALoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify MFA code during login flow.
    
    This endpoint validates the TOTP code or backup code after initial
    password authentication (which should provide a temporary token).
    """
    # Note: In production, implement temporary token validation
    # For now, this is a placeholder for the MFA verification logic
    
    # TODO: Validate temp_token and extract user_id
    # TODO: Check MFA code against stored secret
    # TODO: Issue final access token upon success
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="MFA login verification not yet implemented"
    )


@router.post("/disable")
async def disable_mfa(
    request: MFADisableRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Disable MFA for user account.
    
    Requires current password and TOTP code for security.
    """
    # Get MFA record
    stmt = select(UserMFATable).where(
        UserMFATable.user_id == user_id,
        UserMFATable.is_enabled == True
    )
    mfa_record = (await db.execute(stmt)).scalars().first()
    
    if not mfa_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account"
        )
    
    # Verify password (implement in production)
    # TODO: Add password verification
    
    # Verify TOTP code
    try:
        secret = _decrypt_secret(mfa_record.secret)
        totp = pyotp.TOTP(secret)
        
        # Check if code is a backup code
        is_backup_code = False
        for hashed_code in mfa_record.backup_codes or []:
            if _verify_backup_code(request.code, hashed_code):
                is_backup_code = True
                # Remove used backup code
                mfa_record.backup_codes.remove(hashed_code)
                break
        
        # If not backup code, verify as TOTP
        if not is_backup_code and not totp.verify(request.code, valid_window=1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA code"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA disable verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify MFA code"
        )
    
    # Disable MFA
    mfa_record.is_enabled = False
    mfa_record.secret = None
    mfa_record.backup_codes = None
    mfa_record.verified_at = None
    await db.commit()
    
    # Get user for logging
    user_stmt = select(UserTable).where(UserTable.id == user_id)
    user = (await db.execute(user_stmt)).scalars().first()
    
    logger.info(f"MFA disabled for user: {user.email}")
    
    return {"message": "MFA disabled successfully", "enabled": False}


@router.get("/status")
async def mfa_status(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get MFA status for current user."""
    stmt = select(UserMFATable).where(UserMFATable.user_id == user_id)
    mfa_record = (await db.execute(stmt)).scalars().first()
    
    if not mfa_record:
        return {
            "enabled": False,
            "setup_pending": False,
        }
    
    return {
        "enabled": mfa_record.is_enabled,
        "setup_pending": not mfa_record.is_enabled and mfa_record.secret is not None,
        "type": mfa_record.mfa_type,
        "enabled_at": mfa_record.verified_at.isoformat() if mfa_record.verified_at else None,
        "backup_codes_remaining": len(mfa_record.backup_codes) if mfa_record.backup_codes else 0,
    }
