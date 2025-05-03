"""
SWIFT Code Database Operations.
"""

import os
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import async_yield_db
from app.services.swift_code_parser import parse_swift_file
from fastapi import HTTPException
from app.models.models import SwiftCode
from app.schemas.swift_code_schema import SwiftCodeCreate, SwiftCodeResponse, CountrySwiftCodesResponse, SwiftCodeEntry
from app.core.logger import logger
from typing import List
from app.core.database import AsyncBase, async_engine


#############################################
# Database Initialization Functions
#############################################


async def create_tables():
    """Create database tables if they don't exist."""
    logger.info("Creating database tables...")
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(AsyncBase.metadata.create_all)
        logger.info("Tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


async def seed_swift_codes():
    """
    Seed the database with SWIFT codes from a file if no data exists.
    """
    logger.info("Checking if SWIFT codes data exists...")

    file_path = os.environ.get(
        "SWIFT_CODES_PATH", os.path.join(os.path.dirname(__file__), "data", "Interns_2025_SWIFT_CODES.xlsx")
    )

    async for db in async_yield_db():
        try:
            result = await db.execute(select(SwiftCode).limit(1))
            if result.fetchone():
                logger.info("SWIFT codes already exist in the database. Skipping seed.")
                break

            logger.info("No SWIFT codes found in the database. Seeding from file...")

            parsed_input = parse_swift_file(file_path)
            if parsed_input.empty:
                logger.warning(f"No data found in SWIFT codes file: {file_path}")
                break

            logger.info(f"Successfully parsed SWIFT codes file with {len(parsed_input)} entries")

            await save_swift_codes(parsed_input, db)
            logger.info("Successfully saved SWIFT codes to the database")
            break
        except Exception as e:
            logger.error(f"Error checking or seeding database: {e}")
            raise


async def save_swift_codes(df: pd.DataFrame, db: AsyncSession) -> None:
    """
    Save parsed SWIFT codes from a DataFrame to the database.
    """
    try:
        _validate_swift_file_columns(df)

        logger.info("Started saving SWIFT codes to the database")

        records = df.to_dict("records")

        swift_codes = []
        for record in records:
            swift_code = SwiftCode(
                swift_code=record["SWIFT CODE"],
                name=record["NAME"],
                address=record["ADDRESS"],
                country_iso2=record["COUNTRY ISO2 CODE"],
                country_name=record["COUNTRY NAME"],
                is_headquarter=record["Is Headquarters"],
                headquarters_code=record["Headquarters CODE"],
            )
            swift_codes.append(swift_code)

        db.add_all(swift_codes)
        await db.commit()

        logger.info(f"Successfully saved {len(df)} SWIFT codes to database")
    except Exception as ex:
        await db.rollback()
        logger.error(f"Error saving data to the database: {ex}")
        raise


#############################################
# Read Operations
#############################################


async def get_swift_code_details(swift_code: str, db: AsyncSession) -> SwiftCodeResponse:
    """
    Retrieve details of a specific SWIFT code.
    """
    swift_details = await _fetch_swift_code_from_db(swift_code, db)
    if swift_details.is_headquarter:
        branches = await _fetch_branches_for_hq(swift_code, db)
        return _construct_swift_code_response(swift_details, branches)
    return _construct_swift_code_response(swift_details)


async def fetch_swift_codes_by_country(country_iso2: str, db: AsyncSession) -> List[SwiftCode]:
    """
    Fetch all SWIFT codes for a given country.
    """
    result = await db.execute(select(SwiftCode).where(SwiftCode.country_iso2 == country_iso2.upper()))
    swift_codes = result.scalars().all()
    if not swift_codes:
        raise HTTPException(status_code=404, detail="No SWIFT codes found for this country")
    return swift_codes


#############################################
# Write Operations
#############################################


async def add_swift_code(swift_data: SwiftCodeCreate, db: AsyncSession) -> dict:
    """
    Add a new SWIFT code to the database.
    """
    result = await db.execute(select(SwiftCode).where(SwiftCode.swift_code == swift_data.swiftCode))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=409, detail="SWIFT code already exists")

    new_entry = SwiftCode(
        address=swift_data.address,
        name=swift_data.bankName,
        country_iso2=swift_data.countryISO2.upper(),
        country_name=swift_data.countryName,
        is_headquarter=swift_data.isHeadquarter,
        swift_code=swift_data.swiftCode,
        headquarters_code=None if swift_data.isHeadquarter else "",
    )

    db.add(new_entry)
    try:
        await db.commit()
        await db.refresh(new_entry)
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error adding SWIFT code {swift_data.swiftCode}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add SWIFT code")

    return {"message": "SWIFT code added successfully", "swiftCode": new_entry.swift_code}


async def delete_swift_code(swift_code: str, db: AsyncSession) -> dict:
    """
    Delete a SWIFT code from the database.
    """
    result = await db.execute(select(SwiftCode).where(SwiftCode.swift_code == swift_code))
    entry_to_delete = result.scalars().first()
    if not entry_to_delete:
        raise HTTPException(status_code=404, detail="SWIFT code not found")

    await db.delete(entry_to_delete)
    try:
        await db.commit()
        return {"message": f"SWIFT code {swift_code} deleted successfully"}
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error deleting SWIFT code {swift_code}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete SWIFT code")


#############################################
# Response Formatting
#############################################


def construct_country_swift_code_response(
    country_iso2: str, country_name: str, swift_codes: List[SwiftCode]
) -> CountrySwiftCodesResponse:
    """
    Construct a response containing SWIFT codes for a specific country.
    """
    return CountrySwiftCodesResponse(
        countryISO2=country_iso2,
        countryName=country_name,
        swiftCodes=[
            SwiftCodeEntry(
                address=code.address,
                bankName=code.name,
                countryISO2=code.country_iso2,
                isHeadquarter=code.is_headquarter,
                swiftCode=code.swift_code,
            )
            for code in swift_codes
        ],
    )


#############################################
# Private Helper Functions
#############################################


def _validate_swift_file_columns(df: pd.DataFrame) -> None:
    """
    Validate that required columns are present in the DataFrame.
    """
    required_columns = [
        "SWIFT CODE",
        "NAME",
        "ADDRESS",
        "COUNTRY ISO2 CODE",
        "COUNTRY NAME",
        "Is Headquarters",
        "Headquarters CODE",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {', '.join(missing_columns)}")
        raise KeyError(f"Missing required columns: {', '.join(missing_columns)}")


async def _fetch_swift_code_from_db(swift_code: str, db: AsyncSession) -> SwiftCode:
    """
    Fetch a SWIFT code from the database.
    """
    logger.info(f"Fetching details for SWIFT code: {swift_code}")
    result = await db.execute(select(SwiftCode).where(SwiftCode.swift_code == swift_code))
    swift_details = result.scalars().first()
    if not swift_details:
        logger.warning(f"SWIFT code {swift_code} not found")
        raise HTTPException(status_code=404, detail="SWIFT code not found")
    return swift_details


async def _fetch_branches_for_hq(swift_code: str, db: AsyncSession) -> List[dict]:
    """
    Fetch branches for a headquarters SWIFT code.
    """
    logger.info(f"Fetching branches for HQ SWIFT code: {swift_code}")
    result = await db.execute(select(SwiftCode).where(SwiftCode.headquarters_code == swift_code))
    branches = result.scalars().all()
    return [
        {
            "address": branch.address,
            "bankName": branch.name,
            "countryISO2": branch.country_iso2,
            "countryName": branch.country_name,
            "isHeadquarter": branch.is_headquarter,
            "swiftCode": branch.swift_code,
        }
        for branch in branches
    ]


def _construct_swift_code_response(swift_details: SwiftCode, branch_details: List[dict] = None) -> SwiftCodeResponse:
    """
    Construct a response for a SWIFT code.
    """
    return SwiftCodeResponse(
        address=swift_details.address,
        bankName=swift_details.name,
        countryISO2=swift_details.country_iso2,
        countryName=swift_details.country_name,
        isHeadquarter=swift_details.is_headquarter,
        swiftCode=swift_details.swift_code,
        branches=branch_details or [],
    )
