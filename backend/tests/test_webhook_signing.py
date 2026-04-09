import hmac
import hashlib
import json
from backend.utils.webhook_signing import generate_webhook_signature, validate_webhook_signature


def test_generate_webhook_signature_is_stable():
    secret = "supersecret"
    data = {
        "event": "booking.created",
        "createdAt": "2026-04-09T10:00:00Z",
        "data": {"booking": {"id": "abc123", "email": "guest@example.com"}},
    }

    expected_payload = json.dumps(data, separators=(",", ":"), sort_keys=True)
    expected = hmac.new(secret.encode("utf-8"), expected_payload.encode("utf-8"), hashlib.sha256).hexdigest()

    assert generate_webhook_signature(secret, data) == expected


def test_validate_webhook_signature_returns_true_for_matching_signature():
    secret = "supersecret"
    data = {"hello": "world", "array": [1, 2, 3]}
    signature = generate_webhook_signature(secret, data)
    payload = json.dumps(data, separators=(",", ":"), sort_keys=True)

    assert validate_webhook_signature(secret, payload, signature)


def test_validate_webhook_signature_rejects_invalid_signature():
    secret = "supersecret"
    data = {"hello": "world"}
    signature = "bad-signature"
    payload = json.dumps(data, separators=(",", ":"), sort_keys=True)

    assert not validate_webhook_signature(secret, payload, signature)
