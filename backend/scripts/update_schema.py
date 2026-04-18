"""One-shot schema updater: applies canonical ordered migrations to the main DB.

Run this from the repo root with the project's venv active:

    .venv/Scripts/Activate.ps1
    python backend/scripts/update_schema.py

This mirrors startup behavior but exits immediately after migrations finish.
"""

import logging
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.services.migrations import run_migrations

logger = logging.getLogger("update_schema")


def main():
    try:
        result = run_migrations()
        logger.info(f"Migration summary: {result}")
        print("Schema update: OK")
    except Exception as exc:
        logger.exception("Schema update failed")
        print("Schema update failed:", exc)


if __name__ == "__main__":
    main()
