"""
Calendar Feature Setup Script
Adds description and location fields to the events table
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from backend.utils.db import get_async_session_maker

async def migrate_calendar_schema():
    """Add description and location columns to events table"""
    print("🚀 Starting calendar schema migration...")
    
    SessionLocal = get_async_session_maker()
    async with SessionLocal() as db:
        try:
            # Check if columns already exist
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'events' 
                AND column_name IN ('description', 'location')
            """)
            result = await db.execute(check_query)
            existing_columns = [row[0] for row in result.fetchall()]
            
            if 'description' in existing_columns and 'location' in existing_columns:
                print("✅ Columns already exist. No migration needed.")
                return
            
            # Add description column if it doesn't exist
            if 'description' not in existing_columns:
                print("📝 Adding 'description' column...")
                await db.execute(text("""
                    ALTER TABLE events 
                    ADD COLUMN IF NOT EXISTS description TEXT
                """))
                print("✅ Description column added")
            
            # Add location column if it doesn't exist
            if 'location' not in existing_columns:
                print("📍 Adding 'location' column...")
                await db.execute(text("""
                    ALTER TABLE events 
                    ADD COLUMN IF NOT EXISTS location VARCHAR
                """))
                print("✅ Location column added")
            
            await db.commit()
            print("🎉 Calendar schema migration completed successfully!")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(migrate_calendar_schema())
