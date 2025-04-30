import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from app.services.swift_code_parser import parse_swift_file, save_swift_codes
from app.models.models import SwiftCode
from app.core.database import SessionLocal, Base, engine
from sqlalchemy import text


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


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_db_session():
    session = SessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE"))
    session.commit()
    yield session
    session.close()


@pytest.fixture()
def batch_swift_data():
    return pd.DataFrame(
        {
            "SWIFT CODE": [f"CODE{i:03d}" for i in range(105)],
            "NAME": ["Bank"] * 105,
            "ADDRESS": ["Address"] * 105,
            "COUNTRY ISO2 CODE": ["US"] * 105,
            "COUNTRY NAME": ["United States"] * 105,
            "Is Headquarters": [False] * 105,
            "Headquarters CODE": ["CODE000"] * 105,
        }
    )


def test_parse_swift_file(tmp_path, sample_data, expected_data):
    temp_file = tmp_path / "test_swift_file.xlsx"
    sample_data.to_excel(temp_file, index=False)

    result = parse_swift_file(temp_file)

    assert_frame_equal(result, expected_data)


def test_parse_swift_file_exception_handling(caplog):
    invalid_file_path = "dummy_path.xlsx"

    _ = parse_swift_file(invalid_file_path)

    assert "Error parsing file" in caplog.text
    assert "[Errno 2] No such file or directory: 'dummy_path.xlsx'" in caplog.text


def test_save_swift_codes_success(mock_db_session, tmp_path, sample_data):
    temp_file = tmp_path / "test_swift_file.xlsx"
    sample_data.to_excel(temp_file, index=False)

    parsed_data = parse_swift_file(temp_file)

    save_swift_codes(parsed_data, mock_db_session)

    db_entries = mock_db_session.query(SwiftCode).limit(4).all()
    assert len(db_entries) == len(parsed_data)

    for entry, (_, row) in zip(db_entries, parsed_data.iterrows()):
        assert entry.swift_code == row["SWIFT CODE"]
        assert entry.name == row["NAME"]
        assert entry.address == row["ADDRESS"]
        assert entry.country_iso2 == row["COUNTRY ISO2 CODE"]
        assert entry.country_name == row["COUNTRY NAME"]
        assert entry.is_headquarter == row["Is Headquarters"]
        assert entry.headquarters_code == row["Headquarters CODE"]


def test_save_swift_codes_exception_handling(mock_db_session, sample_data):
    invalid_data = sample_data.drop(columns=["SWIFT CODE"])

    with pytest.raises(KeyError):
        save_swift_codes(invalid_data, mock_db_session)

    db_entries = mock_db_session.query(SwiftCode).all()
    assert len(db_entries) == 0


def test_save_swift_codes_generic_exception_handling(mocker, mock_db_session, sample_data):
    mocker.patch.object(mock_db_session, "add_all", side_effect=Exception("Mocked database error"))

    with pytest.raises(Exception):
        save_swift_codes(sample_data, mock_db_session)

    db_entries = mock_db_session.query(SwiftCode).all()
    assert len(db_entries) == 0
