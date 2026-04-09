import hashlib
import copy
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import UserTable

API_KEY_PREFIX = "gai_"
API_KEY_NAME_MAX_LEN = 80


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _normalize_preferences(user: UserTable) -> Dict[str, Any]:
    prefs = user.preferences or {}
    if not isinstance(prefs, dict):
        return {}
    return copy.deepcopy(prefs)


def _normalize_key_name(name: Optional[str]) -> str:
    normalized = (name or "API Key").strip() or "API Key"
    return normalized[:API_KEY_NAME_MAX_LEN]


def _public_key_record(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": record.get("id"),
        "name": record.get("name"),
        "prefix": record.get("prefix"),
        "created_at": record.get("created_at"),
        "last_used_at": record.get("last_used_at"),
        "revoked_at": record.get("revoked_at"),
        "is_active": not bool(record.get("revoked_at")),
    }


def list_user_api_keys(user: UserTable) -> List[Dict[str, Any]]:
    prefs = _normalize_preferences(user)
    raw_keys = prefs.get("api_keys") or []
    if not isinstance(raw_keys, list):
        return []

    records = [item for item in raw_keys if isinstance(item, dict)]
    records.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return [_public_key_record(record) for record in records]


def create_user_api_key(user: UserTable, name: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
    prefs = _normalize_preferences(user)
    raw_keys = prefs.get("api_keys") or []
    if not isinstance(raw_keys, list):
        raw_keys = []

    raw_key = f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
    record = {
        "id": uuid.uuid4().hex,
        "name": _normalize_key_name(name),
        "prefix": raw_key[:16],
        "hash": _hash_api_key(raw_key),
        "created_at": _utc_iso_now(),
        "last_used_at": None,
        "revoked_at": None,
    }
    raw_keys.append(record)
    prefs["api_keys"] = raw_keys
    user.preferences = prefs

    return _public_key_record(record), raw_key


def revoke_user_api_key(user: UserTable, key_id: str) -> bool:
    prefs = _normalize_preferences(user)
    raw_keys = prefs.get("api_keys") or []
    if not isinstance(raw_keys, list):
        return False

    changed = False
    for record in raw_keys:
        if not isinstance(record, dict):
            continue
        if record.get("id") == key_id and not record.get("revoked_at"):
            record["revoked_at"] = _utc_iso_now()
            changed = True

    if changed:
        prefs["api_keys"] = raw_keys
        user.preferences = prefs

    return changed


def _find_matching_key_record(user: UserTable, candidate_key: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    prefs = _normalize_preferences(user)
    raw_keys = prefs.get("api_keys") or []
    if not isinstance(raw_keys, list):
        return None

    candidate_hash = _hash_api_key(candidate_key)
    candidate_prefix = candidate_key[:16]

    for record in raw_keys:
        if not isinstance(record, dict):
            continue
        if record.get("revoked_at"):
            continue
        if record.get("prefix") != candidate_prefix:
            continue
        if not secrets.compare_digest(str(record.get("hash") or ""), candidate_hash):
            continue
        return record, prefs

    return None


async def resolve_user_by_api_key(
    db: AsyncSession,
    candidate_key: str,
    *,
    track_usage: bool = True,
) -> Optional[UserTable]:
    if not candidate_key or not candidate_key.startswith(API_KEY_PREFIX):
        return None

    result = await db.execute(select(UserTable).where(UserTable.preferences.is_not(None)))
    users = result.scalars().all()

    for user in users:
        matched = _find_matching_key_record(user, candidate_key)
        if not matched:
            continue

        record, prefs = matched
        if track_usage:
            record["last_used_at"] = _utc_iso_now()
            prefs["api_keys"] = prefs.get("api_keys") or []
            user.preferences = prefs
            await db.commit()
            await db.refresh(user)
        return user

    return None
