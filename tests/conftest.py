"""
Tests configuration and fixtures.
"""

import asyncio
import os
from httpx import ASGITransport, AsyncClient
import pytest
import pandas as pd
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.logger import logger
from app.models.models import SwiftCode
from app.schemas.swift_code_schema import SwiftCodeCreate

# Database Configuration for Testing
#############################################

# Fallback for local testing
DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
DB_PORT = os.getenv("TEST_DB_PORT", "5433")
DB_USER = os.getenv("TEST_DB_USER", "swift_user")
DB_PASS = os.getenv("TEST_DB_PASS", "swift_pass")
DB_NAME = os.getenv("TEST_DB_NAME", "test_swift_db")

TEST_DATABASE_URL = (
    os.getenv("TEST_DATABASE_URL") or f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

if os.environ.get("USE_DB_MOCK", "false").lower() != "true":
    async_engine = create_async_engine(TEST_DATABASE_URL, echo=True)
else:
    async_engine = None


#############################################
# Core Test Setup
#############################################


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Setup test database or provide mocks if USE_DB_MOCK is true."""
    if os.environ.get("USE_DB_MOCK", "false").lower() == "true":
        logger.info("Using mocked database - skipping real DB setup")
        yield
        return

    from app.core.database import AsyncBase
    from alembic.config import Config

    logger.info(f"Using TEST_DATABASE_URL: {TEST_DATABASE_URL}")

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)

    async with async_engine.begin() as conn:
        logger.info("Creating test database schema...")
        await conn.run_sync(AsyncBase.metadata.create_all)

    yield

    async with async_engine.begin() as conn:
        logger.info("Dropping test database schema...")
        await conn.run_sync(AsyncBase.metadata.drop_all)


#############################################
# FastAPI App Fixtures
#############################################


@pytest.fixture
def patched_app():
    with (
        patch("app.crud.swift_code_crud.create_tables", new_callable=AsyncMock),
        patch("app.crud.swift_code_crud.seed_swift_codes", new_callable=AsyncMock),
    ):
        from app.main import app

        yield app


@pytest.fixture
def client(patched_app):
    return TestClient(patched_app)


@pytest.fixture
async def async_test_client(patched_app):
    transport = ASGITransport(app=patched_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_app():
    return MagicMock(spec=FastAPI)


#############################################
# Mock Fixtures for Unit Testing
#############################################


@pytest.fixture
def mock_create_tables():
    return AsyncMock()


@pytest.fixture
def mock_seed_swift_codes():
    return AsyncMock()


@pytest.fixture
def mock_create_tables_with_error():
    return AsyncMock(side_effect=Exception("Database error"))


@pytest.fixture
def mock_db_session():
    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.add_all = MagicMock()
    mock_session.delete = AsyncMock()

    return mock_session


@pytest.fixture
def mock_async_session():
    mock_db = AsyncMock()
    mock_db.__aenter__.return_value = mock_db
    mock_db.__aexit__.return_value = None
    yield mock_db


class AsyncContextManagerMock:
    def __init__(self, return_value=None, exception=None):
        self.return_value = return_value
        self.exception = exception

    async def __aenter__(self):
        if self.exception:
            raise self.exception
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def async_context_manager_factory():
    def _factory(return_value=None, exception=None):
        return AsyncContextManagerMock(return_value, exception)

    return _factory


@pytest.fixture
async def async_yield_db():
    """
    Override the app's database session dependency with a mock or real db session.
    """
    if os.environ.get("USE_DB_MOCK", "false").lower() == "true":
        mock_session = AsyncMock()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.add_all = MagicMock()
        mock_session.delete = AsyncMock()

        yield mock_session
    else:
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            yield session


#############################################
# Data Model Fixtures
#############################################


@pytest.fixture
def sample_swift_code():
    return SwiftCode(
        swift_code="TESTCODE123",
        name="Test Bank",
        address="123 Test St",
        country_iso2="US",
        country_name="UNITED STATES",
        is_headquarter=True,
        headquarters_code="TESTCODE123",
    )


@pytest.fixture
def sample_branch_swift_code():
    return SwiftCode(
        swift_code="TESTCODE456",
        name="Test Bank Branch",
        address="456 Branch St",
        country_iso2="US",
        country_name="UNITED STATES",
        is_headquarter=False,
        headquarters_code="TESTCODE123",
    )


@pytest.fixture
def sample_swift_code_create():
    return SwiftCodeCreate(
        address="123 New St",
        bankName="New Bank",
        countryISO2="GB",
        countryName="UNITED KINGDOM",
        isHeadquarter=True,
        swiftCode="NEWCODE123",
    )


@pytest.fixture
def test_swift_code_data():
    return {
        "address": "123 Test St",
        "bankName": "Test Bank",
        "countryISO2": "PL",
        "countryName": "POLAND",
        "isHeadquarter": True,
        "swiftCode": "TESTCODE123",
    }


#############################################
# DataFrame Fixtures for Testing
#############################################


@pytest.fixture
def valid_df():
    return pd.DataFrame(
        {
            "SWIFT CODE": ["TESTCODE1", "TESTCODE2"],
            "NAME": ["Test Bank 1", "Test Bank 2"],
            "ADDRESS": ["123 Test St", "456 Test Ave"],
            "COUNTRY ISO2 CODE": ["US", "GB"],
            "COUNTRY NAME": ["UNITED STATES", "UNITED KINGDOM"],
            "Is Headquarters": [True, False],
            "Headquarters CODE": ["TESTCODE1", "TESTCODE1"],
        }
    )


@pytest.fixture
def invalid_swift_df():
    return pd.DataFrame(
        {
            "SWIFT CODE": ["TESTCODE1"],
            "NAME": ["Test Bank 1"],
        }
    )


@pytest.fixture
def sample_data():
    return pd.DataFrame(
        {
            "SWIFT CODE": ["BANKUS33XXX", "BANKUS33ABC", "BANKGB22XXX", "BANKGB22DEF"],
            "COUNTRY ISO2 CODE": ["us", "us", "gb", "gb"],
            "COUNTRY NAME": ["united states", "united states", "united kingdom", "united kingdom"],
            "TIME ZONE": ["EST", "EST", "GMT", "GMT"],
            "NAME": ["Bank A", "Bank A", "Bank B", "Bank B"],
            "ADDRESS": ["address a", "address b", "address c", "address d"],
        }
    )


@pytest.fixture
def expected_data():
    return pd.DataFrame(
        {
            "SWIFT CODE": ["BANKUS33XXX", "BANKUS33ABC", "BANKGB22XXX", "BANKGB22DEF"],
            "COUNTRY ISO2 CODE": ["US", "US", "GB", "GB"],
            "COUNTRY NAME": ["UNITED STATES", "UNITED STATES", "UNITED KINGDOM", "UNITED KINGDOM"],
            "NAME": ["Bank A", "Bank A", "Bank B", "Bank B"],
            "ADDRESS": ["address a", "address b", "address c", "address d"],
            "Is Headquarters": [True, False, True, False],
            "Headquarters CODE": ["BANKUS33XXX", "BANKUS33XXX", "BANKGB22XXX", "BANKGB22XXX"],
        }
    )
