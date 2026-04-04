import os
import sys
import pytest
import asyncio

# Add the backend package root to PYTHONPATH so tests can import with 'import backend.*'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Ensure deterministic behavior for AI service unit tests using stubbed LLM path
os.environ.setdefault('FORCE_GROQ', '1')
os.environ.setdefault('TESTING', '1')
os.environ.setdefault('DISABLE_CSRF', '1')

@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def bootstrap_test_schema(event_loop):
    """Create DB schema once per test session for SQLite in-memory CI runs."""

    from backend.utils import db as db_utils
    from backend.models.tables import Base as ModelsBase

    async def _create_schema():
        if db_utils.engine is not None:
            async with db_utils.engine.begin() as conn:
                await conn.run_sync(ModelsBase.metadata.create_all)

    async def _dispose_engine():
        if db_utils.engine is not None:
            await db_utils.engine.dispose()

    event_loop.run_until_complete(_create_schema())
    yield
    event_loop.run_until_complete(_dispose_engine())