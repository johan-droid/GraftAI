"""
Passwordless auth module with Redis-backed OTP storage.
"""
from datetime import datetime, timedelta
import random
import json
import os
import redis
from .auth_utils import canonical_email

# Redis client for OTP storage
_redis_client = None

def _get_redis_client():
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client

OTP_TTL_SECONDS = 300


def request_magic_link(email: str):
    code = f"{random.randint(100000, 999999)}"
    expiry = datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS)
    email = canonical_email(email)
    client = _get_redis_client()
    otp_data = json.dumps({"code": code, "expires": expiry.isoformat()})
    client.setex(f"otp:{email}", OTP_TTL_SECONDS, otp_data)

    # In production, send via email provider; here, we log it accessible for tests.
    return {
        "email": email,
        "code": code,
        "expires_at": expiry.isoformat(),
        "message": "OTP code generated; in production, send via email/SMS.",
    }


def verify_magic_link_code(email: str, code: str):
    email = canonical_email(email)
    client = _get_redis_client()
    raw_data = client.get(f"otp:{email}")
    if not raw_data:
        return False
    
    entry = json.loads(raw_data)
    if entry.get("code") != code:
        return False

    if datetime.utcnow() > datetime.fromisoformat(entry.get("expires")):
        client.delete(f"otp:{email}")
        return False

    client.delete(f"otp:{email}")
    return True

