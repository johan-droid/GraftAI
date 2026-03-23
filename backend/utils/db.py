import os
from dotenv import load_dotenv

# Ensure backend/.env is loaded when app is run from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

engine = None
AsyncSessionLocal = None

if DATABASE_URL:
    try:
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker

        engine = create_async_engine(DATABASE_URL, echo=False, future=True)
        AsyncSessionLocal = sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
    except Exception as e:
        print(f"⚠ Database engine creation failed: {e}")
else:
    print("⚠ DATABASE_URL not set — database features disabled")


async def get_db():
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "Database not configured. Set DATABASE_URL in your .env file."
        )
    async with AsyncSessionLocal() as session:
        yield session
