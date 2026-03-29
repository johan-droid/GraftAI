import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

import pytest

@pytest.mark.asyncio
async def test_conn():
    url = os.getenv("DATABASE_URL")
    print(f"Connecting to: {url}")
    try:
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT 1"))
            print(f"Success: {res.fetchone()}")
        await engine.dispose()
    except Exception as e:
        print(f"Error: {e}")
