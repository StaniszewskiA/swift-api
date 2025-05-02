import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from unittest.mock import AsyncMock, MagicMock
from app.services.swift_code_parser import parse_swift_file
from app.core.database import AsyncBase, async_engine


@pytest.fixture(scope="module", autouse=True)
async def setup_test_db():
    """Setup and teardown the test database"""
    async with async_engine.begin() as conn:
        await conn.run_sync(AsyncBase.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(AsyncBase.metadata.drop_all)


@pytest.fixture
def mock_db_session():
    """Create a mocked database session for unit tests"""
    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    return mock_session


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


@pytest.mark.asyncio
async def test_parse_swift_file(tmp_path, sample_data, expected_data):
    """Test parsing SWIFT code file works correctly"""
    temp_file = tmp_path / "test_swift_file.xlsx"
    sample_data.to_excel(temp_file, index=False)

    result = parse_swift_file(temp_file)

    assert_frame_equal(result, expected_data)


@pytest.mark.asyncio
async def test_parse_swift_file_exception_handling(caplog):
    """Test handling of file read errors when parsing SWIFT codes"""
    invalid_file_path = "dummy_path.xlsx"

    _ = parse_swift_file(invalid_file_path)

    assert "Error parsing file" in caplog.text
    assert "[Errno 2] No such file or directory: 'dummy_path.xlsx'" in caplog.text
