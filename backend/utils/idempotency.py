"""
Idempotency key handling for mutation endpoints.
Prevents duplicate operations when clients retry requests.
"""
import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Header, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import IdempotencyKeyTable
from backend.utils.logger import get_logger

logger = get_logger(__name__)
IDEMPOTENCY_KEY_TTL_HOURS = 24

async def check_idempotency_key(db: AsyncSession, key: str, user_id: str, request_body: dict[str, Any]) -> dict[str, Any] | None:
    """
    Check if an idempotency key exists and matches the request.

    Returns:
        The cached response if key exists and matches, None otherwise.

    Raises:
        HTTPException: If key exists but request doesn't match (409 Conflict).
    """
    if not key:
        return None
    import random
    if random.random() < 0.01:
        await _cleanup_expired_keys(db)
    stmt = select(IdempotencyKeyTable).where(IdempotencyKeyTable.key == key, IdempotencyKeyTable.user_id == user_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if not existing:
        return None
    current_fingerprint = _compute_request_fingerprint(request_body)
    if existing.request_fingerprint != current_fingerprint:
        logger.warning("Idempotency key mismatch for user %s...: key=%s... fingerprint mismatch", user_id[:8], key[:16])
        raise HTTPException(status_code=409, detail="Idempotency key already used with different request parameters.")
    logger.info("Idempotency cache hit for user %s...: key=%s...", user_id[:8], key[:16])
    return existing.response_body

async def store_idempotency_key(db: AsyncSession, key: str, user_id: str, request_body: dict[str, Any], response_body: dict[str, Any], status_code: int=200) -> None:
    """Store an idempotency key with its response for future deduplication."""
    if not key:
        return
    fingerprint = _compute_request_fingerprint(request_body)
    expires_at = datetime.now(UTC) + timedelta(hours=IDEMPOTENCY_KEY_TTL_HOURS)
    idempotency_record = IdempotencyKeyTable(key=key, user_id=user_id, request_fingerprint=fingerprint, response_body=response_body, status_code=status_code, expires_at=expires_at)
    db.add(idempotency_record)
    await db.commit()
    logger.debug("Stored idempotency key for user %s...: key=%s...", user_id[:8], key[:16])

async def _cleanup_expired_keys(db: AsyncSession) -> None:
    """Remove expired idempotency keys."""
    stmt = delete(IdempotencyKeyTable).where(IdempotencyKeyTable.expires_at < datetime.now(UTC))
    result = await db.execute(stmt)
    await db.commit()
    if result.rowcount > 0:
        logger.info("Cleaned up %s expired idempotency keys", result.rowcount)

def _compute_request_fingerprint(request_body: dict[str, Any]) -> str:
    """
    Compute a fingerprint of the request body for idempotency comparison.
    Ignores fields that change between retries (like timestamps).
    """
    ignored_fields = {"client_timestamp", "request_id", "nonce"}
    fingerprint_data = {k: v for k, v in request_body.items() if k not in ignored_fields and v is not None}
    canonical = json.dumps(fingerprint_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]

async def idempotency_key_header(idempotency_key: str | None=Header(None, alias="Idempotency-Key")) -> str | None:
    """Extract idempotency key from header."""
    return idempotency_key
