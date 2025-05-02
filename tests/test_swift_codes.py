import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.crud.swift_code_crud import (
    get_swift_code_details,
    fetch_swift_codes_by_country,
    construct_country_swift_code_response,
    add_swift_code,
    delete_swift_code,
)
from app.models.models import SwiftCode
from app.schemas.swift_code_schema import SwiftCodeCreate


@pytest.fixture
def mock_db_session():
    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result

    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.add_all = MagicMock()
    mock_session.delete = AsyncMock()

    return mock_session


@pytest.fixture
def sample_swift_code():
    """Create a sample SwiftCode object"""
    return SwiftCode(
        swift_code="TESTCODE123",
        name="Test Bank",
        address="123 Test St",
        country_iso2="US",
        country_name="UNITED STATES",
        is_headquarter=True,
        headquarters_code="TESTCODE123",
    )


@pytest.fixture
def sample_branch_swift_code():
    """Create a sample branch SwiftCode object"""
    return SwiftCode(
        swift_code="TESTCODE456",
        name="Test Bank Branch",
        address="456 Branch St",
        country_iso2="US",
        country_name="UNITED STATES",
        is_headquarter=False,
        headquarters_code="TESTCODE123",
    )


@pytest.fixture
def sample_swift_code_create():
    """Create a sample SwiftCodeCreate object"""
    return SwiftCodeCreate(
        address="123 New St",
        bankName="New Bank",
        countryISO2="GB",
        countryName="UNITED KINGDOM",
        isHeadquarter=True,
        swiftCode="NEWCODE123",
    )


@pytest.mark.asyncio
async def test_fetch_swift_codes_by_country_success(mock_db_session, sample_swift_code):
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [sample_swift_code]
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    result = await fetch_swift_codes_by_country("US", mock_db_session)

    assert len(result) == 1
    assert result[0].country_iso2 == "US"
    assert result[0].swift_code == "TESTCODE123"


@pytest.mark.asyncio
async def test_fetch_swift_codes_by_country_not_found(mock_db_session):
    with pytest.raises(HTTPException) as exc_info:
        await fetch_swift_codes_by_country("XX", mock_db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No SWIFT codes found for this country"


@pytest.mark.asyncio
async def test_add_swift_code_success(mock_db_session, sample_swift_code_create):
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    result = await add_swift_code(sample_swift_code_create, mock_db_session)

    assert result["message"] == "SWIFT code added successfully"
    assert result["swiftCode"] == "NEWCODE123"

    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_add_swift_code_duplicate(mock_db_session, sample_swift_code, sample_swift_code_create):
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = sample_swift_code
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await add_swift_code(sample_swift_code_create, mock_db_session)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "SWIFT code already exists"
    mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_delete_swift_code_success(mock_db_session, sample_swift_code):
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = sample_swift_code
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    result = await delete_swift_code("TESTCODE123", mock_db_session)

    assert result["message"] == "SWIFT code TESTCODE123 deleted successfully"
    mock_db_session.delete.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_swift_code_not_found(mock_db_session):
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await delete_swift_code("NULL", mock_db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "SWIFT code not found"
    mock_db_session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_get_swift_code_details_hq(mock_db_session, sample_swift_code, sample_branch_swift_code):
    mock_result1 = MagicMock()
    mock_scalars1 = MagicMock()
    mock_scalars1.first.return_value = sample_swift_code
    mock_result1.scalars.return_value = mock_scalars1

    mock_result2 = MagicMock()
    mock_scalars2 = MagicMock()
    mock_scalars2.all.return_value = [sample_branch_swift_code]
    mock_result2.scalars.return_value = mock_scalars2

    mock_db_session.execute.side_effect = [mock_result1, mock_result2]

    result = await get_swift_code_details("TESTCODE123", mock_db_session)

    assert result.swiftCode == "TESTCODE123"
    assert result.isHeadquarter is True
    assert len(result.branches) == 1
    assert result.branches[0].swiftCode == "TESTCODE456"
    assert result.branches[0].bankName == "Test Bank Branch"

    assert mock_db_session.execute.call_count == 2


@pytest.mark.asyncio
async def test_get_swift_code_details_non_hq(mock_db_session, sample_branch_swift_code):
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = sample_branch_swift_code
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    result = await get_swift_code_details("TESTCODE456", mock_db_session)

    assert result.swiftCode == "TESTCODE456"
    assert result.isHeadquarter is False
    assert len(result.branches) == 0

    assert mock_db_session.execute.call_count == 1


def test_construct_country_swift_code_response(sample_swift_code, sample_branch_swift_code):
    country_iso2 = "US"
    country_name = "UNITED STATES"
    swift_codes = [sample_swift_code, sample_branch_swift_code]

    response = construct_country_swift_code_response(country_iso2, country_name, swift_codes)

    assert response.countryISO2 == country_iso2
    assert response.countryName == country_name
    assert len(response.swiftCodes) == 2

    assert response.swiftCodes[0].swiftCode == "TESTCODE123"
    assert response.swiftCodes[0].bankName == "Test Bank"
    assert response.swiftCodes[0].address == "123 Test St"
    assert response.swiftCodes[0].countryISO2 == "US"
    assert response.swiftCodes[0].isHeadquarter is True

    assert response.swiftCodes[1].swiftCode == "TESTCODE456"
    assert response.swiftCodes[1].bankName == "Test Bank Branch"
    assert response.swiftCodes[1].address == "456 Branch St"
    assert response.swiftCodes[1].countryISO2 == "US"
    assert response.swiftCodes[1].isHeadquarter is False


@pytest.mark.asyncio
async def test_add_swift_code_db_error(mock_db_session, sample_swift_code_create):
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    mock_db_session.commit.side_effect = SQLAlchemyError("Database error")

    with pytest.raises(HTTPException) as exc_info:
        await add_swift_code(sample_swift_code_create, mock_db_session)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to add SWIFT code"

    mock_db_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_delete_swift_code_db_error(mock_db_session, sample_swift_code):
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = sample_swift_code
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    mock_db_session.commit.side_effect = SQLAlchemyError("Database error")

    with pytest.raises(HTTPException) as exc_info:
        await delete_swift_code("TESTCODE123", mock_db_session)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to delete SWIFT code"

    mock_db_session.rollback.assert_called_once()
