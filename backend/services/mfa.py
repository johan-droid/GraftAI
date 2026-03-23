"""
MFA and device fingerprinting implementation with TOTP.
"""
import pyotp
from typing import Optional

# In-memory store for user secrets (demo only)
_mfa_secret_store: dict[int, str] = {}


def start_mfa_enrollment(user_id: int) -> dict:
    secret = pyotp.random_base32()
    _mfa_secret_store[user_id] = secret
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=f"user{user_id}@graftai", issuer_name="GraftAI")
    return {"user_id": user_id, "secret": secret, "otp_uri": otp_uri}


def verify_mfa_token(user_id: int, token: str) -> bool:
    secret: Optional[str] = _mfa_secret_store.get(user_id)
    if not secret:
        return False

    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)


def check_device_fingerprint(user_id: int, fingerprint: str) -> bool:
    # Simplified: in production store fingerprints in DB and compare risk thresholds.
    return True

