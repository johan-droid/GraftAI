import logging
from sqlalchemy import text
from backend.utils.db import engine

logger = logging.getLogger(__name__)

async def repair_database():
    """
    Checks for database schema inconsistencies and applies manual patches.
    This is used as a lightweight alternative to migrations for critical production fixes.
    """
    if engine is None:
        logger.warning("Database engine not initialized. Skipping repair.")
        return

    if engine.dialect.name == "sqlite":
        logger.info("SQLite detected: skipping PostgreSQL-specific schema repair.")
        return

    try:
        async with engine.begin() as conn:
            # 1. Check for 'title' column in 'notifications' table
            # We use information_schema which is standard for PostgreSQL
            check_column_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'notifications' AND column_name = 'title';
            """)
            
            result = await conn.execute(check_column_sql)
            has_title = result.fetchone() is not None
            
            if not has_title:
                logger.info("🔧 [REPAIR] Column 'title' missing in 'notifications' table. Patching...")
                await conn.execute(text("ALTER TABLE notifications ADD COLUMN title VARCHAR(255) DEFAULT 'Notification' NOT NULL;"))
                logger.info("✅ [REPAIR] 'notifications' table successfully updated with 'title' column.")
            # 1b. Check for 'data' column in 'notifications' table
            check_data_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'notifications' AND column_name = 'data';
            """)
            result = await conn.execute(check_data_sql)
            if result.fetchone() is None:
                logger.info("🔧 [REPAIR] Column 'data' missing in 'notifications' table. Patching...")
                # Note: JSONB is PostgreSQL specific, use JSON for others if needed but we are on Postgres on Render
                await conn.execute(text("ALTER TABLE notifications ADD COLUMN data JSONB DEFAULT '{}' NOT NULL;"))
                logger.info("✅ [REPAIR] 'notifications' table successfully updated with 'data' column.")
            else:
                logger.info("✅ [REPAIR] 'notifications' table schema verified (data column exists).")


            # 2. Check for user profile detailing columns in the 'users' table
            user_columns = ["bio", "job_title", "location"]
            for col in user_columns:
                check_col_sql = text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = '{col}';
                """)
                res = await conn.execute(check_col_sql)
                if res.fetchone() is None:
                    col_type = "TEXT" if col == "bio" else "VARCHAR(255)"
                    logger.info(f"🔧 [REPAIR] Column '{col}' missing in 'users' table. Patching...")
                    await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type};"))
                    logger.info(f"✅ [REPAIR] 'users' table successfully updated with '{col}' column.")

            # 3. Phase 1: Security & RBAC Columns
            security_cols = {
                "role": "VARCHAR(20) DEFAULT 'member' NOT NULL",
                "mfa_enabled": "BOOLEAN DEFAULT FALSE NOT NULL",
                "mfa_secret": "VARCHAR(128)"
            }
            for col, col_data in security_cols.items():
                res = await conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = '{col}';"))
                if res.fetchone() is None:
                    logger.info(f"🔧 [REPAIR] Security Column '{col}' missing in 'users' table. Patching...")
                    await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_data};"))
                    logger.info(f"✅ [REPAIR] 'users' table successfully updated with security column '{col}'.")

    except Exception as e:
        logger.error(f"❌ [REPAIR] Database repair failed: {e}", exc_info=True)

if __name__ == "__main__":
    # Manual execution if needed
    import asyncio
    asyncio.run(repair_database())
