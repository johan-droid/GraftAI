"""
RBAC/ABAC (roles/attributes) implementation with Redis-backed storage.
"""
from typing import Any, List
import json
import os
import redis

# Redis client for roles and attributes
_redis_client = None

def _get_redis_client():
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
    return _redis_client


def _init_default_roles():
    """Initialize default roles for users 1 and 2 if not exists."""
    client = _get_redis_client()
    if not client.exists("roles:1"):
        client.set("roles:1", json.dumps(["admin"]))
    if not client.exists("roles:2"):
        client.set("roles:2", json.dumps(["user"]))
    if not client.exists("attrs:1"):
        client.set("attrs:1", json.dumps({"tier": "enterprise", "region": "us-east"}))
    if not client.exists("attrs:2"):
        client.set("attrs:2", json.dumps({"tier": "starter", "region": "us-west"}))


def check_user_role(user_id: int, role: str) -> bool:
    _init_default_roles()
    client = _get_redis_client()
    roles_json = client.get(f"roles:{user_id}")
    if not roles_json:
        return False
    roles = json.loads(roles_json)
    return role in roles


def check_user_attribute(user_id: int, attribute: str, value: Any) -> bool:
    _init_default_roles()
    client = _get_redis_client()
    attrs_json = client.get(f"attrs:{user_id}")
    if not attrs_json:
        return False
    attrs = json.loads(attrs_json)
    return attrs.get(attribute) == value

