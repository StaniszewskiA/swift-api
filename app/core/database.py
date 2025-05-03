"""
Database configuration.
"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://swift_user:swift_pass@localhost:5432/swift_db")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

engine_url = TEST_DATABASE_URL if os.getenv("PYTEST_CURRENT_TEST") else DATABASE_URL
async_engine = create_async_engine(engine_url)
AsyncSessionLocal = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
AsyncBase = declarative_base()


async def async_yield_db():
    """
    Provides an async DB session.
    """
    async with AsyncSessionLocal() as session:
        yield session
