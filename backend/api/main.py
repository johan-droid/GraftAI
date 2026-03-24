import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is on sys.path so `import backend...` works even when the process starts from inside backend/
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load env FIRST so all modules can read env vars
dotenv_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=dotenv_path)

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

# --- Self-pinger background task ---
import threading
import time
import httpx

def self_pinger():
    """Background task to keep the service awake by hitting the public URL."""
    # Preferred: Use public URL to trigger external router activity
    public_url = os.getenv("APP_BASE_URL", "https://graftai.onrender.com").rstrip("/")
    health_url = f"{public_url}/health"
    
    # Also keep a local check just in case
    local_url = "http://localhost:8000/health"
    
    while True:
        try:
            # Ping public URL to keep Render awake
            httpx.get(health_url, timeout=10.0)
            # Ping local URL for internal health
            httpx.get(local_url, timeout=5.0)
        except Exception:
            pass
        # Ping every 30 seconds
        time.sleep(30)

# Start the self-pinger in a background thread
threading.Thread(target=self_pinger, daemon=True).start()

# CORS — read allowed origins from env, fallback to local dev + production frontend
_cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://graft-ai-two.vercel.app")
_frontend_url = os.getenv("FRONTEND_BASE_URL")

_cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]
if _frontend_url:
    _cors_origins.append(_frontend_url.strip())

# Remove duplicates while preserving order
_cors_origins = list(dict.fromkeys(_cors_origins))

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


from backend.utils import db as db_utils
from backend.models.tables import Base as ModelsBase


@app.on_event("startup")
async def create_database_tables():
    if not db_utils.engine:
        print("⚠ Database engine is not configured; skipping auto-migration.")
        return
    try:
        async with db_utils.engine.begin() as conn:
            await conn.run_sync(ModelsBase.metadata.create_all)
        print("✅ Database tables verified/created successfully.")
    except Exception as e:
        print(f"⚠ Failed to create or verify database tables: {e}")


@app.get("/")
def root():
    return {"message": "GraftAI Backend API is running."}


@app.get("/health")
def health():
    return {"status": "ok"}
