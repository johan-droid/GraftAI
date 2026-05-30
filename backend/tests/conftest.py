"""
Pytest configuration and shared fixtures for GraftAI backend tests.

Isolation strategy
──────────────────
We use a *single* SQLite in-memory database for the entire test session
(created once, dropped once).  Each test gets its own nested transaction
(SAVEPOINT) so that the test's INSERT/UPDATE/DELETE statements are rolled
back at teardown and never visible to other tests.

Why SAVEPOINT and not a new connection per test?
  - SQLite in-memory databases are connection-local.  StaticPool keeps one
    connection alive for the session so all fixtures share the same schema.
  - Without SAVEPOINT, flush() inside a fixture commits to the shared
    connection and the row is visible to every subsequent test, causing
    UNIQUE-constraint failures when pytest-randomly changes execution order.
"""
import os
import sys
import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import asyncio

from backend.api.deps import get_current_user
from backend.api.main import create_app
from backend.models.base import Base
from backend.models.tables import BookingTable, EventTable, UserTable
from backend.utils.db import get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop."""
    try:
        loop = asyncio.get_event_loop_policy().get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True, connect_args={"check_same_thread": False}, poolclass=StaticPool)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Create all tables once before the session; drop them after."""
    async with test_engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
        except (OperationalError, ProgrammingError) as exc:
            if "already exists" in str(exc).lower():
                pass
            else:
                raise
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """
    Yield a single connection wrapped in a transaction that is rolled back
    after each test.  All sessions within the test share this connection so
    that SAVEPOINT semantics work correctly with SQLite.
    """
    async with test_engine.connect() as conn:
        await conn.begin()
        yield conn
        await conn.rollback()

@pytest_asyncio.fixture
async def db_session(db_connection: AsyncConnection) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional session bound to the per-test connection.
    Uses a SAVEPOINT so every flush/execute inside the test is rolled back
    at teardown without touching data from other tests.
    """
    session_factory = async_sessionmaker(bind=db_connection, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False, join_transaction_mode="create_savepoint")
    async with session_factory() as session:
        yield session
        await session.rollback()

@pytest.fixture
def test_user_data():
    """Return unique test user data per test (avoids UNIQUE conflicts)."""
    suffix = uuid.uuid4().hex[:8]
    return {"id": str(uuid.uuid4()), "email": f"test_{suffix}@example.com", "username": f"testuser_{suffix}", "full_name": "Test User", "hashed_password": "$2b$12$test_hash", "timezone": "UTC", "email_verified": True, "tier": "free", "subscription_status": "inactive", "created_at": datetime.now(UTC)}

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_user_data) -> UserTable:
    """Create and return a test user inside the test's savepoint."""
    user = UserTable(**test_user_data)
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def other_test_user(db_session: AsyncSession, test_user_data) -> UserTable:
    """Create and return a second (distinct) test user inside the same savepoint."""
    suffix = uuid.uuid4().hex[:8]
    other_data = {**test_user_data, "id": str(uuid.uuid4()), "email": f"other_{suffix}@example.com", "username": f"otheruser_{suffix}"}
    user = UserTable(**other_data)
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def authenticated_user(db_session: AsyncSession, test_user: UserTable) -> UserTable:
    """Return an authenticated test user."""
    return test_user

@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Override the get_db dependency for testing."""

    async def _override():
        yield db_session
    return _override

@pytest.fixture
def override_get_current_user(test_user: UserTable):
    """Override the get_current_user dependency for testing."""

    async def _override():
        return test_user
    return _override

@pytest.fixture
def test_app(override_get_db, override_get_current_user) -> FastAPI:
    """Create a test FastAPI application with overridden dependencies."""
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    return app

@pytest.fixture
def unauthenticated_test_app(override_get_db) -> FastAPI:
    """Create a test FastAPI application that always rejects authentication."""
    app = create_app()

    async def _raise_unauthenticated():
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _raise_unauthenticated
    return app

@pytest.fixture
def override_get_current_other_user(other_test_user: UserTable):
    """Override get_current_user for a second authenticated user."""

    async def _override():
        return other_test_user
    return _override

@pytest_asyncio.fixture
async def async_client_for_other_user(override_get_db, override_get_current_other_user) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client authenticated as a second test user."""
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_other_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as client:
        yield client

@pytest_asyncio.fixture
async def async_client_unauthenticated(unauthenticated_test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async client with no authenticated user."""
    transport = ASGITransport(app=unauthenticated_test_app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as client:
        yield client

@pytest_asyncio.fixture
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for API testing."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as client:
        yield client

@pytest.fixture
def sync_client(test_app: FastAPI) -> Generator[TestClient, None, None]:
    """Provide a sync HTTP client for API testing."""
    with TestClient(test_app, base_url="http://localhost") as client:
        yield client

@pytest.fixture
def test_event_data(test_user: UserTable):
    """Return standard test event data."""
    return {"id": str(uuid.uuid4()), "user_id": test_user.id, "title": "Test Meeting", "description": "Test event description", "start_time": datetime.now(UTC), "end_time": datetime.now(UTC), "source": "graftai", "fingerprint": str(uuid.uuid4())}

@pytest_asyncio.fixture
async def test_event(db_session: AsyncSession, test_event_data) -> EventTable:
    """Create and return a test event."""
    event = EventTable(**test_event_data)
    db_session.add(event)
    await db_session.flush()
    await db_session.refresh(event)
    return event

@pytest.fixture
def test_booking_data(test_user: UserTable, test_event: EventTable):
    """Return standard test booking data."""
    return {"id": str(uuid.uuid4()), "user_id": test_user.id, "event_id": test_event.id, "full_name": "Test Booker", "email": "booker@example.com", "status": "confirmed", "start_time": datetime.now(UTC), "end_time": datetime.now(UTC), "time_zone": "UTC", "booking_code": "ABC123"}

@pytest_asyncio.fixture
async def test_booking(db_session: AsyncSession, test_booking_data) -> BookingTable:
    """Create and return a test booking."""
    booking = BookingTable(**test_booking_data)
    db_session.add(booking)
    await db_session.flush()
    await db_session.refresh(booking)
    return booking

@pytest.fixture
def mock_sendgrid(mocker):
    """Mock SendGrid API client."""
    return mocker.patch("backend.ai.tools.communication_tools_real.sendgrid_client")

@pytest.fixture
def mock_twilio(mocker):
    """Mock Twilio API client."""
    return mocker.patch("backend.ai.tools.communication_tools_real.twilio_client")

@pytest.fixture
def mock_llm_core(mocker):
    """Mock LLM core for AI agent tests."""
    return mocker.patch("backend.ai.llm_core.get_llm_core")

@pytest.fixture
def agent_context(test_user: UserTable):
    """Provide standard agent execution context."""
    return {"user_id": test_user.id, "user_message": "Schedule a meeting tomorrow at 2pm", "intent": "schedule_meeting", "entities": {"date": "tomorrow", "time": "14:00", "duration": 30}}
