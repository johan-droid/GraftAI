import os
import sys
from pathlib import Path

# Add backend to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Import the migration service
from backend.services.migrations import run_migrations

migration_file = PROJECT_ROOT / "backend" / "migrations" / "add_sync_tracking_columns.sql"

if __name__ == "__main__":
    print(f"🚀 Running migration: {migration_file.name}...")
    try:
        run_migrations(migration_file=str(migration_file))
        print("✅ Migration applied successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
