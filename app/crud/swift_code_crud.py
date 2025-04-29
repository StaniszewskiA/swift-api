from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import SwiftCode
from app.schemas.swift_code_schema import SwiftCodeCreate, SwiftCodeResponse, CountrySwiftCodesResponse, SwiftCodeEntry
from app.core.logger import logger
from typing import List


def fetch_swift_code_from_db(swift_code: str, db: Session) -> SwiftCode:
    logger.info(f"Fetching details for SWIFT code: {swift_code}")
    swift_details = db.query(SwiftCode).filter(SwiftCode.swift_code == swift_code).first()
    if not swift_details:
        logger.warning(f"SWIFT code {swift_code} not found")
        raise HTTPException(status_code=404, detail="SWIFT code not found")
    return swift_details


def fetch_branches_for_hq(swift_code: str, db: Session) -> List[dict]:
    logger.info(f"Fetching branches for HQ SWIFT code: {swift_code}")
    branches = db.query(SwiftCode).filter(SwiftCode.headquarters_code == swift_code).all()
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


def construct_swift_code_response(swift_details: SwiftCode, branch_details: List[dict] = None) -> SwiftCodeResponse:
    return SwiftCodeResponse(
        address=swift_details.address,
        bankName=swift_details.name,
        countryISO2=swift_details.country_iso2,
        countryName=swift_details.country_name,
        isHeadquarter=swift_details.is_headquarter,
        swiftCode=swift_details.swift_code,
        branches=branch_details or [],
    )


def get_swift_code_details(swift_code: str, db: Session) -> SwiftCodeResponse:
    swift_details = fetch_swift_code_from_db(swift_code, db)
    if swift_details.is_headquarter:
        branches = fetch_branches_for_hq(swift_code, db)
        return construct_swift_code_response(swift_details, branches)
    return construct_swift_code_response(swift_details)


def fetch_swift_codes_by_country(country_iso2: str, db: Session) -> List[SwiftCode]:
    swift_codes = db.query(SwiftCode).filter(SwiftCode.country_iso2 == country_iso2.upper()).all()
    if not swift_codes:
        raise HTTPException(status_code=404, detail="No SWIFT codes found for this country")
    return swift_codes


def construct_country_swift_code_response(
    country_iso2: str, country_name: str, swift_codes: List[SwiftCode]
) -> CountrySwiftCodesResponse:
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


def add_swift_code(swift_data: SwiftCodeCreate, db: Session) -> dict:
    existing = db.query(SwiftCode).filter(SwiftCode.swift_code == swift_data.swiftCode).first()
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
        db.commit()
        db.refresh(new_entry)
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding SWIFT code {swift_data.swiftCode}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add SWIFT code")

    return {"message": "SWIFT code added successfully", "swiftCode": new_entry.swift_code}


def delete_swift_code(swift_code: str, db: Session):
    entry_to_delete = db.query(SwiftCode).filter(SwiftCode.swift_code == swift_code).first()
    if not entry_to_delete:
        raise HTTPException(status_code=404, detail="SWIFT code not found")

    db.delete(entry_to_delete)
    try:
        db.commit()
        return {"message": f"SWIFT code {swift_code} deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting SWIFT code {swift_code}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete SWIFT code")


def save_swift_codes_batch(db: Session, swift_code_entries: list, batch_size: int = 100) -> None:
    """
    Saves a batch of SwiftCode entries to the database.

    Parameters
    ----------
    db : SQLAlchemy session
        Database session to use for saving data
    swift_code_entries : list
        List of SwiftCode objects to save
    batch_size : int, optional
        Number of records to insert in each batch (default is 100)

    Returns
    -------
    None
    """
    for i in range(0, len(swift_code_entries), batch_size):
        logger.info(f"Inserting batch {i // batch_size + 1} of size {batch_size}.")
        db.bulk_save_objects(swift_code_entries[i : i + batch_size])
    db.commit()


def save_swift_codes_to_db(db: Session, swift_code_entries: list) -> None:
    """
    Saves the parsed SWIFT codes from a list of SwiftCode objects to the database.

    Parameters
    ----------
    db : Session
        Database session
    swift_code_entries : list
        List of SwiftCode objects to save

    Returns
    -------
    None
    """
    try:
        save_swift_codes_batch(db, swift_code_entries)
    except Exception as ex:
        db.rollback()
        raise ex
    finally:
        db.close()
