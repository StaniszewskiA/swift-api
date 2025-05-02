import asyncio
import os
import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.logger import logger

# Fallback for local testing
DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
DB_PORT = os.getenv("TEST_DB_PORT", "5433")
DB_USER = os.getenv("TEST_DB_USER", "swift_user")
DB_PASS = os.getenv("TEST_DB_PASS", "swift_pass")
DB_NAME = os.getenv("TEST_DB_NAME", "test_swift_db")

TEST_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not set. Ensure it is defined in your environment or docker-compose.yml.")

async_engine = create_async_engine(TEST_DATABASE_URL, echo=True)


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Ensure all tests use the same event loop."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Set up the test database schema and clean up after tests."""
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
