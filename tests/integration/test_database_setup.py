import pytest
from unittest.mock import AsyncMock, patch
from app.core.database import async_yield_db


@pytest.fixture
def mock_session():
    mock_db = AsyncMock()
    mock_db.__aenter__.return_value = mock_db
    mock_db.__aexit__.return_value = None
    yield mock_db


@pytest.mark.asyncio
async def test_yield_db(mock_session):
    with patch("app.core.database.AsyncSessionLocal", return_value=mock_session):
        db_generator = async_yield_db()
        db = await db_generator.__anext__()

        assert db is mock_session

        await db_generator.aclose()
