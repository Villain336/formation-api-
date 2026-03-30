"""Playwright E2E test configuration.

Starts a live FastAPI server with SQLite for browser + API tests.
"""

import asyncio
import os
import threading
import time

import pytest
import httpx
import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base

# ---------- override DB before importing app ----------
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_e2e.db"
os.environ["APP_ENV"] = "development"
os.environ["SECRET_KEY"] = "test-secret-key-for-e2e-testing"

# Force reload config
import app.core.config
app.core.config.settings = app.core.config.Settings()

# Override the DB engine/session
from app.db import session as db_session_module

_test_engine = create_async_engine("sqlite+aiosqlite:///./test_e2e.db", echo=False)
_test_session_factory = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)
db_session_module.engine = _test_engine
db_session_module.async_session = _test_session_factory


async def _override_get_db():
    async with _test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


from app.main import app
from app.db.session import get_db
app.dependency_overrides[get_db] = _override_get_db

TEST_PORT = 9876
BASE_URL = f"http://localhost:{TEST_PORT}"


async def _create_tables_and_seed():
    """Create all tables and seed with test data using ORM models."""
    from app.models.entity import EntityType, StateRequirement

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with _test_session_factory() as session:
        # Entity types
        session.add_all([
            EntityType(name="llc", display_name="Limited Liability Company (LLC)",
                       description="Flexible business structure."),
            EntityType(name="corporation", display_name="C Corporation",
                       description="Separate legal entity."),
        ])

        # State requirements
        session.add_all([
            StateRequirement(
                state_code="DE", state_name="Delaware", entity_type="llc",
                state_filing_fee=9000, expedited_fee=5000,
                standard_processing_days=3, expedited_processing_days=1,
                filing_agency="Delaware Division of Corporations",
                online_filing_available=True,
                naming_rules={"required_suffix": ["LLC", "L.L.C."]},
            ),
            StateRequirement(
                state_code="WY", state_name="Wyoming", entity_type="llc",
                state_filing_fee=10000, expedited_fee=10000,
                standard_processing_days=5, expedited_processing_days=1,
                filing_agency="Wyoming Secretary of State",
                online_filing_available=True,
            ),
            StateRequirement(
                state_code="NY", state_name="New York", entity_type="llc",
                state_filing_fee=20000, expedited_fee=7500,
                standard_processing_days=7, expedited_processing_days=1,
                requires_publication=True,
                filing_agency="New York DOS",
                naming_rules={"required_suffix": ["LLC", "L.L.C."],
                              "restricted_words": ["bank", "insurance"]},
            ),
            StateRequirement(
                state_code="DE", state_name="Delaware", entity_type="corporation",
                state_filing_fee=8900,
                standard_processing_days=3,
                filing_agency="Delaware Division of Corporations",
                online_filing_available=True,
            ),
        ])
        await session.commit()


def _run_server():
    config = uvicorn.Config(app, host="127.0.0.1", port=TEST_PORT, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


@pytest.fixture(scope="session", autouse=True)
def server():
    """Start the live FastAPI server for E2E tests."""
    if os.path.exists("test_e2e.db"):
        os.remove("test_e2e.db")

    # Create tables and seed
    loop = asyncio.new_event_loop()
    loop.run_until_complete(_create_tables_and_seed())
    loop.close()

    # Start server in daemon thread
    thread = threading.Thread(target=_run_server, daemon=True)
    thread.start()

    # Wait for ready
    for _ in range(30):
        try:
            resp = httpx.get(f"{BASE_URL}/health", timeout=2)
            if resp.status_code == 200:
                break
        except (httpx.ConnectError, httpx.ReadError):
            time.sleep(0.5)
    else:
        pytest.fail("Server did not start in time")

    yield BASE_URL

    if os.path.exists("test_e2e.db"):
        os.remove("test_e2e.db")


@pytest.fixture(scope="session")
def base_url(server):
    return server


@pytest.fixture
def api_url(server):
    return f"{server}/api/v1"
