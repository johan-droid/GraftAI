"""
Passwordless auth module with OTP code support as a service fallback.
"""
from datetime import datetime, timedelta
import random

# In-memory store for OTPs (demo only)
_otp_store: dict[str, dict] = {}

OTP_TTL_SECONDS = 300


def request_magic_link(email: str):
    code = f"{random.randint(100000, 999999)}"
    expiry = datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS)
    _otp_store[email] = {"code": code, "expires": expiry}

    # In production, send via email provider; here, we log it accessible for tests.
    return {
        "email": email,
        "code": code,
        "expires_at": expiry.isoformat(),
        "message": "OTP code generated; in production, send via email/SMS.",
    }


def verify_magic_link_code(email: str, code: str):
    entry = _otp_store.get(email)
    if not entry or entry.get("code") != code:
        return False

    if datetime.utcnow() > entry.get("expires"):
        del _otp_store[email]
        return False

    del _otp_store[email]
    return True

