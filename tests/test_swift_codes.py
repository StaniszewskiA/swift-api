from fastapi.testclient import TestClient
from app.main import app
from app.models.models import SwiftCode
from unittest.mock import MagicMock, patch
import pytest


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_session():
    mock_db = MagicMock()
    mock_db.close = MagicMock()

    mock_filter = MagicMock()
    mock_db.query.return_value = mock_filter

    mock_filter.filter.return_value = mock_filter
    mock_filter.first.return_value = SwiftCode(
        swift_code="ABC123",
        name="Test Bank",
        country_iso2="US",
        country_name="United States",
        is_headquarter=True,
        headquarters_code="HQ123",
        address="Test Address",
    )

    yield mock_db
    mock_db.close()


@patch("app.core.database.SessionLocal", autospec=True)
def test_get_swift_code(mock_db_class, mock_session, client):
    mock_db_class.return_value = mock_session

    response = client.get("/v1/swift-codes/ABC123")

    assert response.status_code == 200
    data = response.json()
    assert data["swiftCode"] == "ABC123"
    assert data["bankName"] == "Test Bank"
    assert data["branches"] == []


@patch("app.core.database.SessionLocal", autospec=True)
def test_get_swift_code_not_found(mock_db_class, mock_session, client):
    mock_db_class.return_value = mock_session
    mock_session.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/v1/swift-codes/Non-existing")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "SWIFT code not found"


@patch("app.core.database.SessionLocal", autospec=True)
def test_get_swift_code_headquarter_only(mock_db_class, mock_session, client):
    mock_db_class.return_value = mock_session

    mock_session.query.return_value.filter.return_value.first.return_value = SwiftCode(
        swift_code="HQ123",
        name="Headquarter Bank",
        country_iso2="US",
        country_name="United States",
        is_headquarter=True,
        headquarters_code=None,
        address="Headquarters Address",
    )

    response = client.get("/v1/swift-codes/HQ123")

    assert response.status_code == 200
    data = response.json()
    assert data["swiftCode"] == "HQ123"
    assert data["bankName"] == "Headquarter Bank"
    assert data["branches"] == []


@patch("app.core.database.SessionLocal", autospec=True)
def test_get_swift_code_with_branches(mock_db_class, mock_session, client):
    mock_db_class.return_value = mock_session

    mock_session.query.return_value.filter.return_value.first.return_value = SwiftCode(
        swift_code="HQ123",
        name="Headquarter Bank",
        country_iso2="US",
        country_name="United States",
        is_headquarter=True,
        headquarters_code=None,
        address="Headquarters Address",
    )

    mock_session.query.return_value.filter.return_value.all.return_value = [
        SwiftCode(
            swift_code="BR123",
            name="Branch Bank 1",
            country_iso2="US",
            country_name="United States",
            is_headquarter=False,
            headquarters_code="HQ123",
            address="Branch 1 Address",
        ),
        SwiftCode(
            swift_code="BR456",
            name="Branch Bank 2",
            country_iso2="US",
            country_name="United States",
            is_headquarter=False,
            headquarters_code="HQ123",
            address="Branch 2 Address",
        ),
    ]

    response = client.get("/v1/swift-codes/HQ123")

    assert response.status_code == 200
    data = response.json()
    assert data["swiftCode"] == "HQ123"
    assert data["bankName"] == "Headquarter Bank"
    assert "branches" in data
    assert len(data["branches"]) == 2
    assert data["branches"][0]["swiftCode"] == "BR123"
    assert data["branches"][0]["bankName"] == "Branch Bank 1"
    assert data["branches"][1]["swiftCode"] == "BR456"
    assert data["branches"][1]["bankName"] == "Branch Bank 2"


@patch("app.core.database.SessionLocal", autospec=True)
def test_get_swift_codes_by_country(mock_db_class, mock_session, client):
    mock_db_class.return_value = mock_session

    mock_session.query.return_value.filter.return_value.all.return_value = [
        SwiftCode(
            swift_code="HQ001",
            name="Test HQ Bank",
            country_iso2="PL",
            country_name="Poland",
            is_headquarter=True,
            headquarters_code=None,
            address="HQ Address",
        ),
        SwiftCode(
            swift_code="BR001",
            name="Test Branch Bank",
            country_iso2="PL",
            country_name="Poland",
            is_headquarter=False,
            headquarters_code="HQ001",
            address="Branch Address",
        ),
    ]

    response = client.get("/v1/swift-codes/country/PL")

    assert response.status_code == 200
    data = response.json()

    assert data["countryISO2"] == "PL"
    assert data["countryName"] == "Poland"
    assert len(data["swiftCodes"]) == 2
    assert data["swiftCodes"][0]["swiftCode"] == "HQ001"
    assert data["swiftCodes"][1]["swiftCode"] == "BR001"


@patch("app.core.database.SessionLocal", autospec=True)
def test_get_swift_codes_by_country_not_found(mock_db_class, mock_session, client):
    mock_db_class.return_value = mock_session
    mock_session.query.return_value.filter.return_value.all.return_value = []

    response = client.get("/v1/swift-code/country/Unknown")

    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"
