
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import select

# Setup paths
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv()

from backend.utils.db import AsyncSessionLocal
from backend.models.tables import EventTable

async def dev_test_db():
    print("--- Testing Database Query for EventTable ---")
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(EventTable).limit(1)
            result = await session.execute(stmt)
            event = result.scalars().first()
            print(f"Success! Found event: {event.title if event else 'No events in DB'}")
        except Exception as e:
            print(f"FAILED: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(dev_test_db())
