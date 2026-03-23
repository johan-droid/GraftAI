"""
RBAC/ABAC (roles/attributes) implementation for basic checks.
"""
from typing import Any

# In-memory role and attribute store (demo only)
_user_roles = {
    1: ["admin"],
    2: ["user"],
}
_user_attributes = {
    1: {"tier": "enterprise", "region": "us-east"},
    2: {"tier": "starter", "region": "us-west"},
}


def check_user_role(user_id: int, role: str) -> bool:
    return role in _user_roles.get(user_id, [])


def check_user_attribute(user_id: int, attribute: str, value: Any) -> bool:
    return _user_attributes.get(user_id, {}).get(attribute) == value

