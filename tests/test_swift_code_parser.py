import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from app.services.swift_code_parser import parse_swift_file, save_swift_codes
from app.models.models import SwiftCode


@pytest.fixture
def sample_data():
    return pd.DataFrame(
        {
            "SWIFT CODE": ["BANKUS33XXX", "BANKUS33ABC", "BANKGB22XXX", "BANKGB22DEF"],
            "COUNTRY ISO2 CODE": ["us", "us", "gb", "gb"],
            "COUNTRY NAME": ["united states", "united states", "united kingdom", "united kingdom"],
            "TIME ZONE": ["EST", "EST", "GMT", "GMT"],
            "BANK NAME": ["Bank A", "Bank A", "Bank B", "Bank B"],
        }
    )


@pytest.fixture
def expected_data():
    return pd.DataFrame(
        {
            "SWIFT CODE": ["BANKUS33XXX", "BANKUS33ABC", "BANKGB22XXX", "BANKGB22DEF"],
            "COUNTRY ISO2 CODE": ["US", "US", "GB", "GB"],
            "COUNTRY NAME": ["UNITED STATES", "UNITED STATES", "UNITED KINGDOM", "UNITED KINGDOM"],
            "BANK NAME": ["Bank A", "Bank A", "Bank B", "Bank B"],
            "Is Headquarters": [True, False, True, False],
            "Headquarters CODE": ["BANKUS33XXX", "BANKUS33XXX", "BANKGB22XXX", "BANKGB22XXX"],
        }
    )


@pytest.fixture
def mock_session():
    class MockSession:
        def __init__(self):
            self.added_entries = []
            self.committed = False
            self.rolled_back = False
            self.closed = False

        def add(self, entry):
            self.added_entries.append(entry)

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

        def close(self):
            self.closed = True

    return MockSession()


def test_parse_swift_file(tmp_path, sample_data, expected_data):
    temp_file = tmp_path / "test_swift_file.xlsx"
    sample_data.to_excel(temp_file, index=False)

    result = parse_swift_file(temp_file)

    assert_frame_equal(result, expected_data)


def test_parse_swift_file_exception_handling(capsys):
    invalid_file_path = "dummy_path.xlsx"

    result = parse_swift_file(invalid_file_path)
    captured = capsys.readouterr()

    assert result is None
    assert "Error parsing file: [Errno 2] No such file or directory: 'dummy_path.xlsx'" in captured.out


def test_save_swift_codes_success_mocked_db(monkeypatch, tmp_path, sample_data, mock_session):
    temp_file = tmp_path / "test_swift_file.xlsx"
    sample_data.to_excel(temp_file, index=False)

    parsed_data = parse_swift_file(temp_file)

    monkeypatch.setattr("app.services.swift_code_parser.SessionLocal", lambda: mock_session)

    save_swift_codes(parsed_data)

    assert len(mock_session.added_entries) == len(parsed_data)
    assert mock_session.committed
    assert mock_session.closed

    for entry, (_, row) in zip(mock_session.added_entries, parsed_data.iterrows()):
        assert isinstance(entry, SwiftCode)
        assert entry.swift_code == row["SWIFT CODE"]
        assert entry.bank_name == row["BANK NAME"]
        assert entry.country_iso2 == row["COUNTRY ISO2 CODE"]
        assert entry.country_name == row["COUNTRY NAME"]
        assert entry.is_headquarter == row["Is Headquarters"]
        assert entry.headquarters_code == row["Headquarters CODE"]


def test_save_swift_codes_exception_handling_mocked_db(monkeypatch, sample_data, mock_session):
    monkeypatch.setattr("app.services.swift_code_parser.SessionLocal", lambda: mock_session)

    def mock_add(entry):
        raise Exception("Database error")

    mock_session.add = mock_add

    save_swift_codes(sample_data)

    assert mock_session.rolled_back
    assert mock_session.closed
