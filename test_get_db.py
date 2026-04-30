import asyncio
import sys
import os

sys.path.append(os.path.abspath('.'))

from backend.utils.db import get_db_context
from sqlalchemy import text

async def main():
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

    # We need to re-import or re-initialize get_db_context with new environment variables
    # Or just use the already defined engine if we hack it

    import importlib
    import backend.utils.db
    importlib.reload(backend.utils.db)

    async with backend.utils.db.get_db_context() as db:
        result = await db.execute(text("SELECT 1 AS num, 'test' AS name"))
        fetched_rows = result.fetchmany(10)

        columns = list(result.keys()) if result.returns_rows else []
        # Result from sqlalchemy returns a sequence of Row objects. We can map them to dicts using `_mapping` or zip
        rows = [dict(zip(columns, row)) for row in fetched_rows]
        print(f"Columns: {columns}")
        print(f"Rows: {rows}")

asyncio.run(main())
