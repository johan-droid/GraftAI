"""
MFA and device fingerprinting implementation with Redis-backed storage.
"""

import pyotp
from backend.utils.redis_singleton import safe_get, safe_set


def start_mfa_enrollment(user_id: int) -> dict:
    secret = pyotp.random_base32()
    safe_set(f"mfa:secret:{user_id}", secret, ttl_seconds=86400)
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=f"user{user_id}@graftai", issuer_name="GraftAI"
    )
    return {"user_id": user_id, "secret": secret, "otp_uri": otp_uri}


def verify_mfa_token(user_id: int, token: str) -> bool:
    secret = safe_get(f"mfa:secret:{user_id}")
    if not secret:
        return False

    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)


def check_device_fingerprint(user_id: int, fingerprint: str) -> bool:
    # Simplified: in production store fingerprints in DB and compare risk thresholds.
    return True
