# --- Self-pinger background task ---
import threading
import time
import requests

def self_pinger():
    while True:
        try:
            # Ping the local health endpoint to keep the server alive
            requests.get("http://localhost:8000/health")
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

# load env from backend/.env if exists (optional for local dev)
from dotenv import load_dotenv
load_dotenv(BACKEND_ROOT / ".env")

from backend.api.main import app  # noqa: E402, F401
