import hashlib
import hmac
import os


def _booking_action_secret() -> str:
    secret = os.getenv("BOOKING_ACTION_SECRET", "").strip()
    if secret:
        return secret

    jwt_secret = os.getenv("JWT_SECRET", "").strip()
    if jwt_secret:
        return jwt_secret

    secret_key = os.getenv("SECRET_KEY", "").strip()
    if secret_key:
        return secret_key

    raise ValueError(
        "BOOKING_ACTION_SECRET, JWT_SECRET, or SECRET_KEY must be configured for booking action tokens."
    )


def create_public_action_token(booking_id: str, email: str) -> str:
    payload = f"{booking_id}:{email.strip().lower()}".encode("utf-8")
    return hmac.new(
        _booking_action_secret().encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()


def verify_public_action_token(booking_id: str, email: str, token: str) -> bool:
    if not token:
        return False
    expected = create_public_action_token(booking_id, email)
    return hmac.compare_digest(expected, token.strip())
