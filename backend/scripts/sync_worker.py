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
    Uses isolated sessions for each user to prevent transaction leakage across external API calls.
    """
    logger.info("🕒 Starting synchronization cycle...")
    start_time = time.time()
    
    # 1. Fetch active targets first (minimal overhead)
    active_tokens = []
    async with AsyncSessionLocal() as db:
        stmt = select(UserTokenTable.id, UserTokenTable.provider).where(UserTokenTable.is_active == True)
        result = await db.execute(stmt)
        active_tokens = result.all() # Returns list of (id, provider)
    
    logger.info(f"🔍 Found {len(active_tokens)} active service connections to sync.")
    
    for token_id, provider in active_tokens:
        try:
            # Create a FRESH session for each provider sync to avoid greenlet/transaction crosstalk
            async with AsyncSessionLocal() as user_db:
                # Re-fetch the token in the current session
                token = await user_db.get(UserTokenTable, token_id)
                if not token or not token.is_active:
                    continue
                    
                logger.info(f"🔄 Syncing {provider} (ID: {token_id})...")
                sync_start = time.time()
                
                if provider == "google":
                    await sync_google_events(user_db, token)
                elif provider == "microsoft":
                    await sync_ms_graph_events(user_db, token)
                
                # We do NOT commit here if sync_ engine handles its own commits/rollbacks
                # but it does help to ensure the session is finished.
                await user_db.commit()
                
                sync_duration = time.time() - sync_start
                logger.info(f"✨ {provider} (ID: {token_id}) synced in {sync_duration:.2f}s")

        except (Exception) as e:
            error_msg = str(e).lower()
            logger.error(f"❌ Failed to sync {provider} (ID: {token_id}): {e}")
            
            # If it's a connection-level error, we might want to dispose the engine pool
            if "connection was closed" in error_msg or "interfaceerror" in error_msg:
                logger.warning("🚨 Database connection lost. Disposing engine pool for recovery.")
                from backend.utils.db import engine
                await engine.dispose()

    duration = time.time() - start_time
    logger.info(f"✅ Sync cycle completed in {duration:.2f} seconds.")

    duration = time.time() - start_time
    logger.info(f"✅ Sync cycle completed in {duration:.2f} seconds.")

async def worker_loop():
    """
    Main worker loop that runs forever.
    """
    logger.info("🚀 GraftAI Smart Sync Worker started.")
    
    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("👋 Received shutdown signal. Gracefully stopping...")
        stop_event.set()

    # Note: signal handlers are only for main thread/UNIX-like, but we can wrap the loop
    # For Windows/WatchFiles, we primarily rely on KeyboardInterrupt catching.
    
    try:
        while not stop_event.is_set():
            try:
                await perform_sync_cycle()
            except Exception as e:
                logger.critical(f"💥 Critical error in worker cycle: {e}")
                
            logger.info(f"💤 Sleeping for {SYNC_INTERVAL_SECONDS} seconds...")
            # Wait for sleep OR stop event
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=SYNC_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                pass
    finally:
        logger.info("🧹 Performing final cleanup...")
        from backend.utils.db import engine
        from backend.utils.cache import get_redis_client
        
        # Dispose engine pool
        await engine.dispose()
        
        # Close Redis
        redis = await get_redis_client()
        if redis:
            await redis.aclose()
            
        logger.info("✨ Cleanup complete. Goodbye!")

if __name__ == "__main__":
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Unexpected exit: {e}")
