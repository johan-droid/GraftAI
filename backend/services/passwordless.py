"""
Passwordless auth module with Redis-backed OTP storage.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
import random
from .auth_utils import canonical_email
from .redis_client import redis_service

logger = logging.getLogger(__name__)

OTP_TTL_SECONDS = 300

async def request_magic_link(email: str):
    """
    Generate and store a magic link OTP in Redis (Async).
    """
    code = f"{random.randint(100000, 999999)}"
    expiry = datetime.now(timezone.utc) + timedelta(seconds=OTP_TTL_SECONDS)
    email = canonical_email(email)
    
    client = redis_service.client
    otp_data = json.dumps({"code": code, "expires": expiry.isoformat()})
    
    try:
        await client.setex(f"otp:{email}", OTP_TTL_SECONDS, otp_data)
        logger.info(f"✨ Magic link generated for {email}")
    except Exception as e:
        logger.error(f"❌ Failed to store OTP for {email}: {e}")
        # In a real SaaS, we'd still return the code here if the mailer was independent,
        # but for this flow we need Redis.

    # In production, send via email provider; here, we log it accessible for tests.
    return {
        "email": email,
        "code": code,
        "expires_at": expiry.isoformat(),
        "message": "OTP code generated; in production, send via email/SMS.",
    }


async def verify_magic_link_code(email: str, code: str) -> bool:
    """
    Verify the magic link OTP from Redis (Async).
    """
    email = canonical_email(email)
    client = redis_service.client
    
    try:
        raw_data = await client.get(f"otp:{email}")
        if not raw_data:
            return False

        entry = json.loads(raw_data)
        if entry.get("code") != code:
            return False

        # Expiry check
        expires_at = datetime.fromisoformat(entry.get("expires"))
        if datetime.now(timezone.utc) > expires_at:
            await client.delete(f"otp:{email}")
            return False

        # One-time use: delete after successful verification
        await client.delete(f"otp:{email}")
        return True
    except Exception as e:
        logger.error(f"❌ OTP verification error for {email}: {e}")
        return False
