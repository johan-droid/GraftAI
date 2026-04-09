import os
import sys
import pytest
import asyncio
import tempfile

# Ensure deterministic behavior for AI service unit tests using stubbed LLM path
os.environ['FORCE_GROQ'] = '1'
os.environ['TESTING'] = '1'
os.environ['DISABLE_CSRF'] = '1'

# Use a temporary SQLite file database for test isolation and cross-thread compatibility.
test_db_file = tempfile.NamedTemporaryFile(prefix='graftai_test_', suffix='.db', delete=False)
test_db_file.close()
os.environ['DATABASE_URL'] = f'sqlite+aiosqlite:///{test_db_file.name}'

# Add the backend package root to PYTHONPATH so tests can import with 'import backend.*'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
def bootstrap_test_schema(event_loop):
    """Create a fresh DB schema for each test using a file-backed SQLite database."""

    from backend.utils import db as db_utils
    from backend.models.tables import Base as ModelsBase

    async def _reset_schema():
        if db_utils.engine is not None:
            async with db_utils.engine.begin() as conn:
                await conn.run_sync(ModelsBase.metadata.drop_all)
                await conn.run_sync(ModelsBase.metadata.create_all)

    event_loop.run_until_complete(_reset_schema())
    yield

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_engine(event_loop):
    yield
    from backend.utils import db as db_utils

    async def _dispose_engine():
        if db_utils.engine is not None:
            await db_utils.engine.dispose()

    event_loop.run_until_complete(_dispose_engine())
    try:
        os.remove(test_db_file.name)
    except FileNotFoundError:
        pass