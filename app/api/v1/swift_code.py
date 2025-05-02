from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_yield_db
from app.schemas.swift_code_schema import SwiftCodeCreate, SwiftCodeResponse, CountrySwiftCodesResponse
from app.crud import swift_code_crud

router = APIRouter(prefix="/v1/swift-codes", tags=["Swift Codes"])


@router.get(
    "/{swift_code}",
    response_model=SwiftCodeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "SWIFT code not found"},
    },
)
async def get_swift_code(swift_code: str, db: AsyncSession = Depends(async_yield_db)):
    """Retrieve details of a SWIFT code."""
    return await swift_code_crud.get_swift_code_details(swift_code, db)


@router.get(
    "/country/{country_iso2code}",
    response_model=CountrySwiftCodesResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No SWIFT codes found for this country"},
    },
)
async def get_swift_codes_by_country(country_iso2code: str, db: AsyncSession = Depends(async_yield_db)):
    """Retrieve SWIFT codes for a specific country."""
    swift_codes = await swift_code_crud.fetch_swift_codes_by_country(country_iso2code, db)
    if not swift_codes:
        return {"country_iso2code": country_iso2code, "country_name": None, "swift_codes": []}
    country_name = swift_codes[0].country_name
    return swift_code_crud.construct_country_swift_code_response(country_iso2code, country_name, swift_codes)


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "SWIFT code already exists"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to add SWIFT code"},
    },
)
async def add_swift_code(swift_data: SwiftCodeCreate, db: AsyncSession = Depends(async_yield_db)):
    """Add a new SWIFT code to the database."""
    response = await swift_code_crud.add_swift_code(swift_data, db)
    return response


@router.delete(
    "/{swift_code}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "SWIFT code not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Failed to delete SWIFT code"},
    },
)
async def delete_swift_code(swift_code: str, db: AsyncSession = Depends(async_yield_db)):
    """Delete a SWIFT code from the database."""
    response = await swift_code_crud.delete_swift_code(swift_code, db)
    return response
