import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def migrate():
    if not DATABASE_URL:
        print("DATABASE_URL not found")
        return

    # Handle asyncpg driver requirement
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(url)
    
    async with engine.begin() as conn:
        print("[*] Adding columns to 'events' table...")
        columns = [
            ("provider_id", "VARCHAR(255)"),
            ("provider_source", "VARCHAR(50)"),
            ("is_busy", "BOOLEAN DEFAULT TRUE NOT NULL")
        ]
        
        for name, type_ in columns:
            try:
                await conn.execute(text(f"ALTER TABLE events ADD COLUMN {name} {type_};"))
                print(f"[+] Added column: {name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"[!] Column {name} already exists, skipping.")
                else:
                    print(f"[!] Error adding {name}: {e}")
        
        # Add indexes
        try:
            await conn.execute(text("CREATE INDEX ix_events_provider_id ON events (provider_id);"))
            await conn.execute(text("CREATE INDEX ix_events_provider_source ON events (provider_source);"))
            print("[+] Added indexes for sync performance.")
        except Exception as e:
            print(f"[!] Index creation skipped: {e}")

    await engine.dispose()
    print("[*] Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
