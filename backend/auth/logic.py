import hashlib
import hmac
import os


def _booking_action_secret() -> str:
    secret = os.getenv("BOOKING_ACTION_SECRET", "").strip()
    if secret:
        return secret
    msg = (
        "BOOKING_ACTION_SECRET must be configured separately from JWT_SECRET/SECRET_KEY "
        "for booking action tokens. Reusing JWT signing keys for HMAC weakens security."
    )
    raise ValueError(msg)

def create_public_action_token(booking_id: str, email: str) -> str:
    payload = f"{booking_id}:{email.strip().lower()}".encode()
    return hmac.new(_booking_action_secret().encode("utf-8"), payload, hashlib.sha256).hexdigest()

def verify_public_action_token(booking_id: str, email: str, token: str) -> bool:
    if not token:
        return False
    expected = create_public_action_token(booking_id, email)
    return hmac.compare_digest(expected, token.strip())
