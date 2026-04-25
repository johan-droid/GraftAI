import asyncio
import sys
import os

# Ensure the parent directory is in sys.path so we can import 'backend'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.utils.db import get_async_session_maker
from backend.models.tables import UserTable
from sqlalchemy import update

async def reset_user_tier():
    Session = get_async_session_maker()
    async with Session() as session:
        # Update all users to 'free' tier if they are currently 'pro' or not set correctly
        stmt = update(UserTable).values(tier="free", subscription_status="inactive")
        await session.execute(stmt)
        await session.commit()
        print("DONE: All users reset to FREE tier.")

if __name__ == "__main__":
    asyncio.run(reset_user_tier())
