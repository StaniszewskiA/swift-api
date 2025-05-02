import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from app.services.swift_code_parser import parse_swift_file


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
