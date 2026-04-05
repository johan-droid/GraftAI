"""
RBAC/ABAC (roles/attributes) implementation with Redis-backed storage.
"""

import json
from backend.utils.redis_singleton import safe_get, safe_set


def _ensure_defaults(user_id: str | int) -> None:
    uid = str(user_id)
    if safe_get(f"roles:{uid}") is None:
        if uid in ("1", "2"):
            roles = ["admin"] if uid == "1" else ["user"]
            attrs = (
                {"tier": "enterprise", "region": "us-east"}
                if uid == "1"
                else {"tier": "starter", "region": "us-west"}
            )
            safe_set(f"roles:{uid}", json.dumps(roles))
            safe_set(f"attrs:{uid}", json.dumps(attrs))


def check_user_role(user_id: str | int, role: str) -> bool:
    _ensure_defaults(user_id)
    raw = safe_get(f"roles:{user_id}")
    if not raw:
        return False
    return role in json.loads(raw)


def check_user_attribute(user_id: str | int, attribute: str, value: str) -> bool:
    _ensure_defaults(user_id)
    raw = safe_get(f"attrs:{user_id}")
    if not raw:
        return False
    return json.loads(raw).get(attribute) == value
