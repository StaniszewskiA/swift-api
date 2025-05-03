"""
Unit test for SWIFT code CRUD operations on mocked database.
"""

import pandas as pd
import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from app.crud.swift_code_crud import (
    get_swift_code_details,
    fetch_swift_codes_by_country,
    construct_country_swift_code_response,
    add_swift_code,
    delete_swift_code,
    save_swift_codes,
)

#############################################
# Database Initialization Tests
#############################################


@pytest.mark.asyncio
async def test_create_tables_success(monkeypatch, async_context_manager_factory):
    mock_conn = AsyncMock()
    mock_async_engine = MagicMock()
    mock_async_engine.begin.return_value = async_context_manager_factory(return_value=mock_conn)

    monkeypatch.setattr("app.crud.swift_code_crud.async_engine", mock_async_engine)

    from app.crud.swift_code_crud import create_tables
    from app.core.database import AsyncBase

    await create_tables()

    mock_async_engine.begin.assert_called_once()
    mock_conn.run_sync.assert_called_once_with(AsyncBase.metadata.create_all)


@pytest.mark.asyncio
async def test_create_table_exception(monkeypatch, async_context_manager_factory):
    mock_async_engine = MagicMock()
    mock_async_engine.begin.return_value = async_context_manager_factory(exception=Exception("DB connection failed"))

    monkeypatch.setattr("app.crud.swift_code_crud.async_engine", mock_async_engine)

    from app.crud.swift_code_crud import create_tables

    with pytest.raises(Exception) as exc_info:
        await create_tables()

    assert "DB connection failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_seed_swift_codes_data_exists(monkeypatch):
    mock_db_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = {"swift_code": "EXISTING"}
    mock_db_session.execute.return_value = mock_result

    async def mock_async_yield_db():
        yield mock_db_session

    monkeypatch.setattr("app.crud.swift_code_crud.async_yield_db", mock_async_yield_db)

    from app.crud.swift_code_crud import seed_swift_codes
    import os

    monkeypatch.setattr(os, "environ", {})

    mock_save = AsyncMock()
    monkeypatch.setattr("app.crud.swift_code_crud.save_swift_codes", mock_save)

    await seed_swift_codes()

    mock_db_session.execute.assert_called_once()
    mock_save.assert_not_called()


@pytest.mark.asyncio
async def test_seed_swift_codes_empty_file(monkeypatch):
    mock_db_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_db_session.execute.return_value = mock_result

    async def mock_async_yield_db():
        yield mock_db_session

    monkeypatch.setattr("app.crud.swift_code_crud.async_yield_db", mock_async_yield_db)

    empty_df = pd.DataFrame()
    monkeypatch.setattr("app.crud.swift_code_crud.parse_swift_file", lambda _: empty_df)

    mock_save = AsyncMock()
    monkeypatch.setattr("app.crud.swift_code_crud.save_swift_codes", mock_save)

    from app.crud.swift_code_crud import seed_swift_codes

    await seed_swift_codes()

    mock_db_session.execute.assert_called_once()
    mock_save.assert_not_called()


@pytest.mark.asyncio
async def test_seed_swift_codes_success(monkeypatch, valid_df):
    mock_db_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_db_session.execute.return_value = mock_result

    async def mock_async_yield_db():
        yield mock_db_session

    monkeypatch.setattr("app.crud.swift_code_crud.async_yield_db", mock_async_yield_db)
    monkeypatch.setattr("app.crud.swift_code_crud.parse_swift_file", lambda _: valid_df)

    mock_save = AsyncMock()
    monkeypatch.setattr("app.crud.swift_code_crud.save_swift_codes", mock_save)

    from app.crud.swift_code_crud import seed_swift_codes

    await seed_swift_codes()

    mock_db_session.execute.assert_called_once()
    mock_save.assert_called_once_with(valid_df, mock_db_session)


@pytest.mark.asyncio
async def test_seed_swift_codes_exception(monkeypatch):
    mock_db_session = AsyncMock()
    mock_db_session.execute.side_effect = Exception("Database error")

    async def mock_async_yield_db():
        yield mock_db_session

    monkeypatch.setattr("app.crud.swift_code_crud.async_yield_db", mock_async_yield_db)

    from app.crud.swift_code_crud import seed_swift_codes

    with pytest.raises(Exception) as exc_info:
        await seed_swift_codes()

    assert "Database error" in str(exc_info.value)
    mock_db_session.execute.assert_called_once()


#############################################
# Read Operation Tests
#############################################


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


@pytest.mark.asyncio
async def test_get_swift_code_details_not_found(mock_db_session):
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as excinfo:
        await get_swift_code_details("NONEXISTENT", mock_db_session)

    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "SWIFT code not found"

    mock_db_session.execute.assert_called_once()


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


#############################################
# Write Operation Tests
#############################################


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


@pytest.mark.asyncio
async def test_save_swift_code_success(mock_db_session, valid_df):
    await save_swift_codes(valid_df, mock_db_session)
    mock_db_session.add_all.assert_called_once()

    args, _ = mock_db_session.add_all.call_args
    swift_codes = args[0]
    assert len(swift_codes) == 2

    assert swift_codes[0].swift_code == "TESTCODE1"
    assert swift_codes[0].name == "Test Bank 1"
    assert swift_codes[0].address == "123 Test St"
    assert swift_codes[0].country_iso2 == "US"
    assert swift_codes[0].country_name == "UNITED STATES"
    assert swift_codes[0].is_headquarter is True
    assert swift_codes[0].headquarters_code == "TESTCODE1"

    mock_db_session.commit.assert_called_once()
    mock_db_session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_save_swift_codes_validation_error(mock_db_session, invalid_swift_df):
    with pytest.raises(KeyError) as exc_info:
        await save_swift_codes(invalid_swift_df, mock_db_session)

    assert "Missing required columns" in str(exc_info)
    mock_db_session.add_all.assert_not_called()
    mock_db_session.commit.assert_not_called()
    mock_db_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_save_swift_codes_db_error(mock_db_session, valid_df):
    mock_db_session.commit.side_effect = SQLAlchemyError("Database error")

    with pytest.raises(SQLAlchemyError):
        await save_swift_codes(valid_df, mock_db_session)

    mock_db_session.add_all.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.rollback.assert_called_once()


#############################################
# Helper Function Tests
#############################################


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
