"""
Pytest configuration and shared fixtures for GraftAI backend tests.
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.models.base import Base
from backend.models.tables import UserTable, EventTable, BookingTable
from backend.api.main import create_app
from backend.utils.db import get_db
from backend.api.deps import get_current_user

# Test database URL (SQLite in-memory for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Session factory
AsyncTestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def setup_test_database():
    """Create test database tables."""
    async with test_engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
        except (OperationalError, ProgrammingError) as exc:
            # Occasionally SQLite create_all will attempt to create an index that
            # already exists (race in metadata generation). Treat that as non-fatal
            # for test setup so unit tests can run reliably in CI/local dev.
            if "already exists" in str(exc).lower():
                pass
            else:
                raise
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session for tests."""
    async with AsyncTestingSessionLocal() as session:

        async def _commit(*_args, **_kwargs):
            await session.flush()

        session.commit = _commit  # type: ignore[assignment]
        yield session
        await session.rollback()


@pytest.fixture
def test_user_data():
    """Return standard test user data."""
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "hashed_password": "$2b$12$test_hash",  # Pre-hashed for tests
        "timezone": "UTC",
        "email_verified": True,
        "tier": "free",
        "subscription_status": "inactive",
        "created_at": datetime.now(timezone.utc),
    }


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_user_data) -> UserTable:
    """Create and return a test user in the database."""
    user = UserTable(**test_user_data)
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_test_user(db_session: AsyncSession, test_user_data) -> UserTable:
    """Create and return a second test user in the database."""
    other_data = {**test_user_data}
    other_data["id"] = str(uuid.uuid4())
    other_data["email"] = "other@example.com"
    other_data["username"] = "otheruser"
    user = UserTable(**other_data)
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def authenticated_user(
    db_session: AsyncSession, test_user: UserTable
) -> UserTable:
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
def test_app(
    override_get_db,
    override_get_current_user,
) -> FastAPI:
    """Create a test FastAPI application with overridden dependencies."""
    app = create_app()

    # Override dependencies
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
async def async_client_for_other_user(
    override_get_db,
    override_get_current_other_user,
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client authenticated as a second test user."""
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_other_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as client:
        yield client


@pytest_asyncio.fixture
async def async_client_unauthenticated(
    unauthenticated_test_app: FastAPI,
) -> AsyncGenerator[AsyncClient, None]:
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


# Event fixtures
@pytest.fixture
def test_event_data(test_user: UserTable):
    """Return standard test event data."""
    return {
        "id": str(uuid.uuid4()),
        "user_id": test_user.id,
        "title": "Test Meeting",
        "description": "Test event description",
        "start_time": datetime.now(timezone.utc),
        "end_time": datetime.now(timezone.utc),
        "source": "graftai",
        "fingerprint": str(uuid.uuid4()),
    }


@pytest_asyncio.fixture
async def test_event(db_session: AsyncSession, test_event_data) -> EventTable:
    """Create and return a test event."""
    event = EventTable(**test_event_data)
    db_session.add(event)
    await db_session.flush()
    await db_session.refresh(event)
    return event


# Booking fixtures
@pytest.fixture
def test_booking_data(test_user: UserTable, test_event: EventTable):
    """Return standard test booking data."""
    return {
        "id": str(uuid.uuid4()),
        "user_id": test_user.id,
        "event_id": test_event.id,
        "name": "Test Booker",
        "email": "booker@example.com",
        "status": "confirmed",
        "start_time": datetime.now(timezone.utc),
        "end_time": datetime.now(timezone.utc),
        "timezone": "UTC",
        "booking_code": "ABC123",
    }


@pytest_asyncio.fixture
async def test_booking(db_session: AsyncSession, test_booking_data) -> BookingTable:
    """Create and return a test booking."""
    booking = BookingTable(**test_booking_data)
    db_session.add(booking)
    await db_session.flush()
    await db_session.refresh(booking)
    return booking


# Mock fixtures for external services
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


# AI Agent test fixtures
@pytest.fixture
def agent_context(test_user: UserTable):
    """Provide standard agent execution context."""
    return {
        "user_id": test_user.id,
        "user_message": "Schedule a meeting tomorrow at 2pm",
        "intent": "schedule_meeting",
        "entities": {
            "date": "tomorrow",
            "time": "14:00",
            "duration": 30,
        },
    }
