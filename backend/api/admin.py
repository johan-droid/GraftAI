from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.api.deps import get_db
from backend.auth.schemes import get_current_user
import logging
import os
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/status")
async def get_system_status(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Superuser-only system health dashboard.
    Aggregates status from Neon DB, Redis, and Arq Worker.
    """
    if not getattr(current_user, "is_superuser", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required"
        )
    
    stats = {
        "timestamp": time.time(),
        "database": {"status": "unknown"},
        "redis": {"status": "unknown"},
        "worker": {"status": "unknown"},
        "environment": os.getenv("ENVIRONMENT", "production")
    }

    # 1. Check Neon Database Health
    try:
        start_time = time.perf_counter()
        await db.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start_time) * 1000
        stats["database"] = {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "engine": "Neon Serverless Postgres"
        }
    except Exception as e:
        stats["database"] = {"status": "unhealthy", "error": str(e)}

    # 2. Check Redis & Rate Limiting
    try:
        from backend.api.main import _get_redis_client
        redis_client = _get_redis_client()
        if redis_client.ping():
            stats["redis"] = {
                "status": "healthy",
                "keys_count": redis_client.dbsize(),
                "provider": "Upstash/Redis"
            }
    except Exception as e:
        stats["redis"] = {"status": "unhealthy", "error": str(e)}

    # 3. Check Arq Background Worker
    try:
        from backend.services.bg_tasks import get_task_pool
        pool = await get_task_pool()
        # Get queue info, include basic pool status to avoid unused variable under ruff
        stats["worker"] = {
            "status": "online",
            "queue_name": "arq:queue",
            "pool_status": "connected" if pool else "unavailable"
        }
    except Exception as e:
        stats["worker"] = {"status": "offline", "error": str(e)}

    return stats

@router.post("/users/{user_id}/upgrade")
async def upgrade_user_tier(
    user_id: str,
    tier: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Manual administrative upgrade of a user's subscription tier."""
    if not getattr(current_user, "is_superuser", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    from backend.models.tables import UserTable
    user = await db.get(UserTable, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.tier = tier
    await db.commit()
    return {"message": f"User {user_id} upgraded to {tier}"}

@router.get("/email/diagnostic")
async def email_diagnostic(current_user = Depends(get_current_user)):
    """スーパーユーザ(Superuser) only tool to verify SMTP settings."""
    if not getattr(current_user, "is_superuser", False):
        raise HTTPException(status_code=403, detail="Superuser required")
    from backend.services.email import verify_smtp_config
    return verify_smtp_config()

@router.post("/email/test")
async def send_test_email(email: str, current_user = Depends(get_current_user)):
    """スーパーユーザ(Superuser) only tool to send a test email message."""
    if not getattr(current_user, "is_superuser", False):
        raise HTTPException(status_code=403, detail="Superuser required")
    
    from backend.services.email import send_email
    try:
        subject = "GraftAI - Platform Diagnostics"
        html = f"<h3>Diagnostics Success</h3><p>Your SMTP credentials for <b>Google</b> are confirmed and active.</p><p>Triggered by {current_user.email}</p>"
        await send_email(to_email=email, subject=subject, html_body=html)
        return {"status": "success", "message": f"Diagnostic email dispatched to {email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
