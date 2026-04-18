import hashlib
import hmac
import json
from typing import Any


def generate_webhook_signature(secret: str, data: Any) -> str:
    payload = json.dumps(data, separators=(",", ":"), sort_keys=True)
    return hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def validate_webhook_signature(secret: str, payload: str, signature: str) -> bool:
    expected_signature = hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)
