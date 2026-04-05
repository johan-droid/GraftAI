"""
Passwordless auth module with Redis-backed OTP storage.
"""

from datetime import datetime, timedelta
import random
import json
from backend.utils.redis_singleton import safe_delete, safe_get, safe_set
from .auth_utils import canonical_email


OTP_TTL_SECONDS = 300


def request_magic_link(email: str):
    code = f"{random.randint(100000, 999999)}"
    expiry = datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS)
    email = canonical_email(email)
    otp_data = json.dumps({"code": code, "expires": expiry.isoformat()})
    safe_set(f"otp:{email}", otp_data, ttl_seconds=OTP_TTL_SECONDS)

    # In production, send via email provider; here, we log it accessible for tests.
    return {
        "email": email,
        "code": code,
        "expires_at": expiry.isoformat(),
        "message": "OTP code generated; in production, send via email/SMS.",
    }


def verify_magic_link_code(email: str, code: str):
    email = canonical_email(email)
    raw_data = safe_get(f"otp:{email}")
    if not raw_data:
        return False

    entry = json.loads(raw_data)
    if entry.get("code") != code:
        return False

    if datetime.utcnow() > datetime.fromisoformat(entry.get("expires")):
        safe_delete(f"otp:{email}")
        return False

    safe_delete(f"otp:{email}")
    return True
