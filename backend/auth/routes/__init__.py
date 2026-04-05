from fastapi import APIRouter
from backend.auth.routes import local, sso, session, advanced

router = APIRouter(prefix="/auth", tags=["auth"])

# Include sub-routers
router.include_router(local.router)
router.include_router(sso.router)
router.include_router(session.router)
router.include_router(advanced.router)

