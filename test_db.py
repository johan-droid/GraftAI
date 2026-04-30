import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath('.'))

from backend.utils.db import get_db_context
from sqlalchemy import text

async def main():
    async with get_db_context() as db:
        result = await db.execute(text("SELECT 1 AS num, 'test' AS name"))
        fetched_rows = result.fetchmany(10)

        columns = list(result.keys()) if result.returns_rows else []
        rows = [dict(zip(columns, row)) for row in fetched_rows]
        print(f"Columns: {columns}")
        print(f"Rows: {rows}")

asyncio.run(main())
