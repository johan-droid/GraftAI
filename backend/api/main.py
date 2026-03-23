import os
from dotenv import load_dotenv

# Load env FIRST so all modules can read env vars
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.auth.routes import router as auth_router
from backend.api.users import router as users_router
from backend.services.ai import router as ai_router
from backend.services.analytics import router as analytics_router
from backend.services.consent import router as consent_router
from backend.services.proactive import router as proactive_router
from backend.services.upgrade import router as upgrade_router
from backend.services.plugin_api import router as plugin_router

app = FastAPI(
    title="GraftAI Backend",
    description="Production API for GraftAI — AI-powered scheduling platform",
    version="1.0.0",
)

# CORS — read allowed origins from env, fallback to localhost for dev
_cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
_cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(ai_router)
app.include_router(analytics_router)
app.include_router(consent_router)
app.include_router(proactive_router)
app.include_router(upgrade_router)
app.include_router(plugin_router)


@app.get("/")
def root():
    return {"message": "GraftAI Backend API is running."}


@app.get("/health")
def health():
    return {"status": "ok"}
