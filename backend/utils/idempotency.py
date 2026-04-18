"""
Idempotency key handling for mutation endpoints.
Prevents duplicate operations when clients retry requests.
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import HTTPException, Header
from backend.models.tables import IdempotencyKeyTable
from backend.utils.logger import get_logger

logger = get_logger(__name__)

IDEMPOTENCY_KEY_TTL_HOURS = 24  # Keys expire after 24 hours


async def check_idempotency_key(
    db: AsyncSession,
    key: str,
    user_id: str,
    request_body: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Check if an idempotency key exists and matches the request.

    Returns:
        The cached response if key exists and matches, None otherwise.

    Raises:
        HTTPException: If key exists but request doesn't match (409 Conflict).
    """
    if not key:
        return None

    # Clean up expired keys periodically (simple probabilistic cleanup)
    import random

    if random.random() < 0.01:  # 1% chance per request
        await _cleanup_expired_keys(db)

    # Look up the key
    stmt = select(IdempotencyKeyTable).where(
        IdempotencyKeyTable.key == key,
        IdempotencyKeyTable.user_id == user_id,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if not existing:
        return None

    # Verify request fingerprint matches
    current_fingerprint = _compute_request_fingerprint(request_body)

    if existing.request_fingerprint != current_fingerprint:
        logger.warning(
            f"Idempotency key mismatch for user {user_id[:8]}...: "
            f"key={key[:16]}... fingerprint mismatch"
        )
        raise HTTPException(
            status_code=409,
            detail="Idempotency key already used with different request parameters.",
        )

    # Return cached response
    logger.info(f"Idempotency cache hit for user {user_id[:8]}...: key={key[:16]}...")
    return existing.response_body


async def store_idempotency_key(
    db: AsyncSession,
    key: str,
    user_id: str,
    request_body: Dict[str, Any],
    response_body: Dict[str, Any],
    status_code: int = 200,
) -> None:
    """Store an idempotency key with its response for future deduplication."""
    if not key:
        return

    fingerprint = _compute_request_fingerprint(request_body)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=IDEMPOTENCY_KEY_TTL_HOURS)

    idempotency_record = IdempotencyKeyTable(
        key=key,
        user_id=user_id,
        request_fingerprint=fingerprint,
        response_body=response_body,
        status_code=status_code,
        expires_at=expires_at,
    )

    db.add(idempotency_record)
    await db.commit()

    logger.debug(f"Stored idempotency key for user {user_id[:8]}...: key={key[:16]}...")


async def _cleanup_expired_keys(db: AsyncSession) -> None:
    """Remove expired idempotency keys."""
    stmt = delete(IdempotencyKeyTable).where(
        IdempotencyKeyTable.expires_at < datetime.now(timezone.utc)
    )
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount > 0:
        logger.info(f"Cleaned up {result.rowcount} expired idempotency keys")


def _compute_request_fingerprint(request_body: Dict[str, Any]) -> str:
    """
    Compute a fingerprint of the request body for idempotency comparison.
    Ignores fields that change between retries (like timestamps).
    """
    # Fields to ignore in fingerprint (client-generated timestamps, etc.)
    ignored_fields = {"client_timestamp", "request_id", "nonce"}

    # Create a copy without ignored fields
    fingerprint_data = {
        k: v
        for k, v in request_body.items()
        if k not in ignored_fields and v is not None
    }

    # Sort keys for consistent hashing
    canonical = json.dumps(fingerprint_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


# FastAPI dependency for idempotency handling
async def idempotency_key_header(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> Optional[str]:
    """Extract idempotency key from header."""
    return idempotency_key
