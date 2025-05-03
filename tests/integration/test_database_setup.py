"""
Integration tests for database connection setup.
"""

import pytest
from unittest.mock import patch
from app.core.database import async_yield_db


@pytest.mark.asyncio
async def test_yield_db(mock_async_session):
    with patch("app.core.database.AsyncSessionLocal", return_value=mock_async_session):
        db_generator = async_yield_db()
        db = await db_generator.__anext__()

        assert db is mock_async_session

        await db_generator.aclose()
