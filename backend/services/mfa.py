"""
MFA and device fingerprinting implementation with Redis-backed storage.
"""

import pyotp
import json
import os
from typing import Optional
import redis

# Redis client for MFA secrets
_redis_client = None


def _get_redis_client():
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


def start_mfa_enrollment(user_id: int) -> dict:
    secret = pyotp.random_base32()
    client = _get_redis_client()
    client.setex(f"mfa:secret:{user_id}", 86400, secret)  # 24h TTL
    otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=f"user{user_id}@graftai", issuer_name="GraftAI"
    )
    return {"user_id": user_id, "secret": secret, "otp_uri": otp_uri}


def verify_mfa_token(user_id: int, token: str) -> bool:
    client = _get_redis_client()
    secret = client.get(f"mfa:secret:{user_id}")
    if not secret:
        return False

    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)


def check_device_fingerprint(user_id: int, fingerprint: str) -> bool:
    # Simplified: in production store fingerprints in DB and compare risk thresholds.
    return True
