"""
FIDO2 and decentralized identity (DID) support with Redis-backed storage.
"""

import uuid
import json
from backend.utils.redis_singleton import safe_delete, safe_get, safe_set


def start_fido2_registration(user_id: int) -> dict:
    challenge = str(uuid.uuid4())
    credential_data = json.dumps({"challenge": challenge, "registered": False})
    safe_set(f"fido:{user_id}", credential_data, ttl_seconds=3600)
    return {"user_id": user_id, "challenge": challenge}


def complete_fido2_registration(user_id: int, attestation: dict) -> bool:
    raw_data = safe_get(f"fido:{user_id}")
    if not raw_data:
        return False

    record = json.loads(raw_data)
    if record.get("registered"):
        return False

    record["registered"] = True
    record["attestation"] = attestation
    safe_set(f"fido:{user_id}", json.dumps(record), ttl_seconds=86400)
    return True


def verify_fido2_assertion(user_id: int, assertion: dict) -> bool:
    raw_data = safe_get(f"fido:{user_id}")
    if not raw_data:
        return False

    record = json.loads(raw_data)
    if not record.get("registered"):
        return False
    return assertion.get("challenge") == record.get("challenge")


def issue_decentralized_id(user_id: int) -> str:
    issued_did = f"did:example:{uuid.uuid4()}"
    safe_set(f"did:{user_id}", issued_did)
    return issued_did


def verify_decentralized_id(user_id: int, did: str) -> bool:
    stored_did = safe_get(f"did:{user_id}")
    return stored_did == did
