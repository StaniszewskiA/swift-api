"""
Unit tests for the SWIFT code file parser service.
"""

import pytest
from pandas.testing import assert_frame_equal
from app.services.swift_code_parser import parse_swift_file


@pytest.mark.asyncio
async def test_parse_swift_file(tmp_path, sample_data, expected_data):
    temp_file = tmp_path / "test_swift_file.xlsx"
    sample_data.to_excel(temp_file, index=False)

    result = parse_swift_file(temp_file)

    assert_frame_equal(result, expected_data)


@pytest.mark.asyncio
async def test_parse_swift_file_exception_handling(caplog):
    invalid_file_path = "dummy_path.xlsx"

    _ = parse_swift_file(invalid_file_path)

    assert "Error parsing file" in caplog.text
    assert "[Errno 2] No such file or directory: 'dummy_path.xlsx'" in caplog.text
