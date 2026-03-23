"""
FIDO2 and decentralized identity (DID) support with demo methods.
"""
import uuid
from typing import Dict

_fido_credential_store: Dict[int, Dict] = {}
_did_registry: Dict[int, str] = {}


def start_fido2_registration(user_id: int) -> dict:
    challenge = str(uuid.uuid4())
    _fido_credential_store[user_id] = {"challenge": challenge, "registered": False}
    return {"user_id": user_id, "challenge": challenge}


def complete_fido2_registration(user_id: int, attestation: dict) -> bool:
    record = _fido_credential_store.get(user_id)
    if not record or record["registered"]:
        return False
    record["registered"] = True
    record["attestation"] = attestation
    return True


def verify_fido2_assertion(user_id: int, assertion: dict) -> bool:
    record = _fido_credential_store.get(user_id)
    if not record or not record.get("registered"):
        return False
    return assertion.get("challenge") == record.get("challenge")


def issue_decentralized_id(user_id: int) -> str:
    issued_did = f"did:example:{uuid.uuid4()}"
    _did_registry[user_id] = issued_did
    return issued_did


def verify_decentralized_id(user_id: int, did: str) -> bool:
    return _did_registry.get(user_id) == did

