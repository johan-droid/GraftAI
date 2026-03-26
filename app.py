# --- Self-pinger background task ---
import threading
import time
import httpx

def self_pinger():
    """Background task to keep the service awake by hitting the public URL."""
    # Wait a bit for the server to start
    time.sleep(10)
    
    public_url = os.getenv("APP_BASE_URL", "https://graftai.onrender.com").rstrip("/")
    health_url = f"{public_url}/health"
    local_url = "http://localhost:8000/health"
    
    while True:
        try:
            httpx.get(health_url, timeout=10.0)
            httpx.get(local_url, timeout=5.0)
        except Exception:
            pass
        time.sleep(30)

# Start the self-pinger in a background thread
threading.Thread(target=self_pinger, daemon=True).start()
"""ASGI entrypoint wrapper for production compatibility.

Use this in environments where command is uvicorn app:app.
It also ensures backend package path is available when current wd is not project root.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# load env from project root or backend/.env if exists (optional for local dev)
from dotenv import load_dotenv
load_dotenv() # Load from current directory first
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_ROOT / ".env")

from backend.api.main import app  # noqa: E402, F401

if __name__ == "__main__":
    import uvicorn
    # Use standard host/port or env vars
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting server on {host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=True, log_level="debug")
