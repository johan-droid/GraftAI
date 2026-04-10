"""API Key management routes for developer access."""

from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from backend.api.deps import get_db, get_current_user
from backend.models.tables import UserTable
from backend.models.api_key import APIKey, APIKeyUsage, generate_api_key, hash_api_key

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


# Pydantic Models

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    scopes: List[str] = Field(default=["read"])
    expires_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: Optional[str] = None  # Only shown on creation
    key_prefix: str
    scopes: List[str]
    is_active: bool
    created_at: str
    expires_at: Optional[str] = None
    last_used_at: Optional[str] = None
    request_count: int


class APIKeyUsageStats(BaseModel):
    total_requests: int
    requests_last_24h: int
    requests_last_7d: int
    top_endpoints: List[dict]


# Helper function to validate API key
async def validate_api_key(
    x_api_key: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> APIKey:
    """Validate API key from header."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Hash the provided key
    key_hash = hash_api_key(x_api_key)
    
    # Find matching key
    stmt = select(APIKey).where(
        and_(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        )
    )
    api_key = (await db.execute(stmt)).scalars().first()
    
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check expiration
    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="API key expired")
    
    # Update last used
    api_key.last_used_at = datetime.now(timezone.utc)
    api_key.request_count += 1
    await db.commit()
    
    return api_key


# Routes

@router.post("/", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Create a new API key."""
    # Generate the key (only shown once)
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[:12]  # First 12 chars for display
    
    # Calculate expiration
    expires_at = None
    if key_data.expires_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=key_data.expires_days)
    
    # Create key record
    api_key = APIKey(
        name=key_data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        user_id=current_user.id,
        scopes=key_data.scopes,
        expires_at=expires_at
    )
    
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,  # Only shown on creation
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        created_at=api_key.created_at.isoformat(),
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
        last_used_at=None,
        request_count=0
    )


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """List all API keys for the current user."""
    stmt = select(APIKey).where(APIKey.user_id == current_user.id).order_by(APIKey.created_at.desc())
    keys = (await db.execute(stmt)).scalars().all()
    
    return [
        APIKeyResponse(
            id=k.id,
            name=k.name,
            key=None,  # Never return the full key
            key_prefix=k.key_prefix,
            scopes=k.scopes,
            is_active=k.is_active,
            created_at=k.created_at.isoformat(),
            expires_at=k.expires_at.isoformat() if k.expires_at else None,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            request_count=k.request_count
        )
        for k in keys
    ]


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Get details of a specific API key."""
    stmt = select(APIKey).where(
        and_(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        )
    )
    api_key = (await db.execute(stmt)).scalars().first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=None,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        is_active=api_key.is_active,
        created_at=api_key.created_at.isoformat(),
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
        last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        request_count=api_key.request_count
    )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Revoke (delete) an API key."""
    stmt = select(APIKey).where(
        and_(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        )
    )
    api_key = (await db.execute(stmt)).scalars().first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    await db.delete(api_key)
    await db.commit()
    
    return {"status": "success", "message": "API key revoked"}


@router.post("/{key_id}/toggle")
async def toggle_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Toggle an API key active/inactive."""
    stmt = select(APIKey).where(
        and_(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        )
    )
    api_key = (await db.execute(stmt)).scalars().first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_key.is_active = not api_key.is_active
    await db.commit()
    
    return {
        "status": "success",
        "is_active": api_key.is_active,
        "message": f"API key {'activated' if api_key.is_active else 'deactivated'}"
    }


@router.get("/{key_id}/usage", response_model=APIKeyUsageStats)
async def get_api_key_usage(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    """Get usage statistics for an API key."""
    # Verify ownership
    stmt = select(APIKey).where(
        and_(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        )
    )
    api_key = (await db.execute(stmt)).scalars().first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Get total requests
    stmt = select(func.count(APIKeyUsage.id)).where(APIKeyUsage.api_key_id == key_id)
    total_requests = (await db.execute(stmt)).scalar() or 0
    
    # Get requests in last 24 hours
    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
    stmt = select(func.count(APIKeyUsage.id)).where(
        and_(
            APIKeyUsage.api_key_id == key_id,
            APIKeyUsage.requested_at >= yesterday
        )
    )
    requests_last_24h = (await db.execute(stmt)).scalar() or 0
    
    # Get requests in last 7 days
    last_week = datetime.now(timezone.utc) - timedelta(days=7)
    stmt = select(func.count(APIKeyUsage.id)).where(
        and_(
            APIKeyUsage.api_key_id == key_id,
            APIKeyUsage.requested_at >= last_week
        )
    )
    requests_last_7d = (await db.execute(stmt)).scalar() or 0
    
    # Get top endpoints
    stmt = select(
        APIKeyUsage.endpoint,
        APIKeyUsage.method,
        func.count(APIKeyUsage.id).label('count')
    ).where(
        APIKeyUsage.api_key_id == key_id
    ).group_by(
        APIKeyUsage.endpoint,
        APIKeyUsage.method
    ).order_by(func.count(APIKeyUsage.id).desc()).limit(10)
    
    top_endpoints = [
        {"endpoint": row.endpoint, "method": row.method, "count": row.count}
        for row in (await db.execute(stmt)).all()
    ]
    
    return APIKeyUsageStats(
        total_requests=total_requests,
        requests_last_24h=requests_last_24h,
        requests_last_7d=requests_last_7d,
        top_endpoints=top_endpoints
    )


# Public endpoint for API key authentication testing
@router.get("/validate/test")
async def test_api_key_auth(
    api_key: APIKey = Depends(validate_api_key)
):
    """Test if an API key is valid."""
    return {
        "valid": True,
        "key_id": api_key.id,
        "name": api_key.name,
        "scopes": api_key.scopes,
        "owner_id": api_key.user_id
    }
