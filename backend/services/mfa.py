"""
MFA and device fingerprinting implementation with Redis-backed storage.
"""

import pyotp
import logging
import os
from .redis_client import redis_service

logger = logging.getLogger(__name__)

async def start_mfa_enrollment(user_id: int) -> dict:
    """
    Generate MFA secret and provisioning URI (Async).
    """
    secret = pyotp.random_base32()
    client = redis_service.client
    
    try:
        await client.setex(f"mfa:secret:{user_id}", 86400, secret)  # 24h TTL
    except Exception as e:
        logger.error(f"❌ Failed to store MFA secret for user {user_id}: {e}")

    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=f"user{user_id}@graftai", issuer_name="GraftAI"
    )
    return {"user_id": user_id, "secret": secret, "otp_uri": otp_uri}


async def verify_mfa_token(user_id: int, token: str) -> bool:
    """
    Verify the MFA token against the stored secret (Async).
    """
    client = redis_service.client
    
    try:
        secret = await client.get(f"mfa:secret:{user_id}")
        if not secret:
            logger.warning(f"⚠ MFA secret not found for user {user_id} (expired or not started)")
            return False

        totp = pyotp.TOTP(secret)
        # Use a window of 1 to allow for slight clock drift
        return totp.verify(token, valid_window=1)
    except Exception as e:
        logger.error(f"❌ MFA verification error for user {user_id}: {e}")
        return False


def check_device_fingerprint(user_id: int, fingerprint: str) -> bool:
    # Simplified: in production store fingerprints in DB and compare risk thresholds.
    return True
