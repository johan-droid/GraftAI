from fastapi import APIRouter
from backend.auth.routes import local, sso, session, advanced
from backend.auth.logic import get_rate_limiter, create_jwt_token

router = APIRouter(prefix="/auth", tags=["auth"])

# Include sub-routers
router.include_router(local.router)
router.include_router(sso.router)
router.include_router(session.router)
router.include_router(advanced.router)

# Exposed helpers for tests and package-level imports
_get_rate_limiter = get_rate_limiter
_create_jwt_token = create_jwt_token

__all__ = [
    "router",
    "_get_rate_limiter",
    "_create_jwt_token",
    "local",
    "sso",
    "session",
    "advanced",
]

