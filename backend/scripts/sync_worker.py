import asyncio
import logging
import time
import os
import sys
from pathlib import Path

# Fix module resolution
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from sqlalchemy import select
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sync-worker")

# Load environment
env_path = ROOT_DIR / ".env"
load_dotenv(env_path)

from backend.models.user_token import UserTokenTable
from backend.services.sync_engine import sync_google_events, sync_ms_graph_events

# Connection logic for Neon (SSL)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found")

# Use existing engine if available, or create new specialized worker engine
from backend.utils.db import AsyncSessionLocal

SYNC_INTERVAL_SECONDS = 300  # 5 minutes

async def perform_sync_cycle():
    """
    One full pass over all active user tokens to sync their calendars.
    """
    logger.info("🕒 Starting synchronization cycle...")
    start_time = time.time()
    
    async with AsyncSessionLocal() as db:
        # 1. Fetch all active tokens
        stmt = select(UserTokenTable).where(UserTokenTable.is_active == True)
        result = await db.execute(stmt)
        tokens = result.scalars().all()
        
        logger.info(f"🔍 Found {len(tokens)} active service connections to sync.")
        
        for token in tokens:
            try:
                if token.provider == "google":
                    await sync_google_events(db, token)
                elif token.provider == "microsoft":
                    await sync_ms_graph_events(db, token)
                # Zoom sync can be added here when meeting:read scope is present
            except Exception as e:
                logger.error(f"❌ Failed to sync {token.provider} for user {token.user_id}: {e}")
                
        await db.commit()

    duration = time.time() - start_time
    logger.info(f"✅ Sync cycle completed in {duration:.2f} seconds.")

async def worker_loop():
    """
    Main worker loop that runs forever.
    """
    logger.info("🚀 GraftAI Smart Sync Worker started.")
    
    while True:
        try:
            await perform_sync_cycle()
        except Exception as e:
            logger.critical(f"💥 Critical error in worker cycle: {e}")
            
        logger.info(f"💤 Sleeping for {SYNC_INTERVAL_SECONDS} seconds...")
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.info("👋 Sync Worker shutting down.")
