"""
FIDO2 and decentralized identity (DID) support with Redis-backed storage.
"""

import uuid
import json
import os
from typing import Dict
import redis

# Redis client for FIDO2 and DID storage
_redis_client = None


def _get_redis_client():
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


def start_fido2_registration(user_id: int) -> dict:
    challenge = str(uuid.uuid4())
    client = _get_redis_client()
    credential_data = json.dumps({"challenge": challenge, "registered": False})
    client.setex(f"fido:{user_id}", 3600, credential_data)  # 1h TTL
    return {"user_id": user_id, "challenge": challenge}


def complete_fido2_registration(user_id: int, attestation: dict) -> bool:
    client = _get_redis_client()
    raw_data = client.get(f"fido:{user_id}")
    if not raw_data:
        return False

    record = json.loads(raw_data)
    if record.get("registered"):
        return False

    record["registered"] = True
    record["attestation"] = attestation
    client.setex(f"fido:{user_id}", 86400, json.dumps(record))  # 24h TTL
    return True


def verify_fido2_assertion(user_id: int, assertion: dict) -> bool:
    client = _get_redis_client()
    raw_data = client.get(f"fido:{user_id}")
    if not raw_data:
        return False

    record = json.loads(raw_data)
    if not record.get("registered"):
        return False
    return assertion.get("challenge") == record.get("challenge")


def issue_decentralized_id(user_id: int) -> str:
    issued_did = f"did:example:{uuid.uuid4()}"
    client = _get_redis_client()
    client.set(f"did:{user_id}", issued_did)  # No expiry for DIDs
    return issued_did


def verify_decentralized_id(user_id: int, did: str) -> bool:
    client = _get_redis_client()
    stored_did = client.get(f"did:{user_id}")
    return stored_did == did
