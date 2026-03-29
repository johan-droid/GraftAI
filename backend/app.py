import os
import sys
import threading
import time
from pathlib import Path

# Third-party imports
import httpx  # type: ignore
from dotenv import load_dotenv  # type: ignore

# --- Virtual Environment Auto-Activation ---
def ensure_venv():
    """If a .venv exists and we are not in it, re-execute with .venv's python."""
    import sys
    import subprocess
    from pathlib import Path

    backend_dir = Path(__file__).resolve().parent
    venv_python = (backend_dir / ".venv" / "Scripts" / "python.exe").resolve()
    current_python = Path(sys.executable).resolve()

    if venv_python.exists() and current_python != venv_python:
        print(f"[*] Switching to virtual environment: {venv_python}", flush=True)
        # Preserve all arguments and re-execute
        cmd = [str(venv_python)] + sys.argv
        sys.exit(subprocess.call(cmd))

# Run venv check BEFORE any other imports that might fail
ensure_venv()

# --- Project Root & Environment Setup ---
BACKEND_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_ROOT.parent

# Ensure project root and backend root are in sys.path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Also set environment variable for sub-processes (uvicorn reloader)
os.environ["PYTHONPATH"] = f"{PROJECT_ROOT}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_ROOT / ".env")

# --- Self-pinger background task ---
def self_pinger():
    """Background task to keep the service awake by hitting the public URL."""
    # Wait a bit for the server to start
    time.sleep(10)
    
    public_url = os.getenv("APP_BASE_URL", "https://graftai.onrender.com").rstrip("/")
    health_url = f"{public_url}/health"
    local_url = "http://127.0.0.1:8000/health"
    
    while True:
        try:
            # Use a context manager for httpx to ensure connection pooling/closing
            with httpx.Client(timeout=10.0) as client:
                client.get(health_url)
                client.get(local_url, timeout=5.0)
        except Exception:
            # Silently fail background ping
            pass
        time.sleep(30)

# Start the self-pinger in a background thread
threading.Thread(target=self_pinger, daemon=True).start()

# --- Backend Application Import ---
# Since we are in the backend folder, we import from api directly
try:
    from api.main import app
except ImportError:
    from backend.api.main import app # Fallback for absolute imports

if __name__ == "__main__":
    import uvicorn  # type: ignore
    # Use standard host/port or env vars
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting server on {host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=True, log_level="debug")
