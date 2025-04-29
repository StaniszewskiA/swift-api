from app.schemas.swift_code_schema import SwiftCodeCreate, CountrySwiftCodesResponse, SwiftCodeEntry, SwiftCodeResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import yield_db
from app.models.models import SwiftCode
from app.core.logger import logger

router = APIRouter(prefix="/v1/swift-codes", tags=["Swift Codes"])


def fetch_swift_code_from_db(swift_code: str, db: Session) -> SwiftCode:
    """
    Fetch SwiftCode details from the database.
    """
    logger.info(f"Fetching details for SWIFT code: {swift_code}")
    swift_details = db.query(SwiftCode).filter(SwiftCode.swift_code == swift_code).first()
    if not swift_details:
        logger.warning(f"SWIFT code {swift_code} not found")
        raise HTTPException(status_code=404, detail="SWIFT code not found")
    logger.info(f"Found SWIFT code: {swift_code} in the database")
    return swift_details


def fetch_branches_for_hq(swift_code: str, db: Session) -> list:
    """
    Fetch branches associated with a given headquarters SWIFT code.
    """
    logger.info(f"Fetching branches for headquarters SWIFT code: {swift_code}")
    branches = db.query(SwiftCode).filter(SwiftCode.headquarters_code == swift_code).all()
    logger.info(f"Found {len(branches)} branches for SWIFT code: {swift_code}")
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


def construct_swift_code_response(swift_details: SwiftCode, branch_details: list = None) -> SwiftCodeResponse:
    """Construct and return a SwiftCodeResponse object."""
    logger.info(f"Constructing response for SWIFT code: {swift_details.swift_code}")
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
    """
    Gets detailed SwiftCode response including branches if applicable
    """
    logger.info(f"Getting details for SWIFT code: {swift_code}")
    swift_details = fetch_swift_code_from_db(swift_code, db)

    if swift_details.is_headquarter:
        logger.info(f"SWIFT code {swift_code} is a headquarter, fetching branches")
        branch_details = fetch_branches_for_hq(swift_code, db)
        return construct_swift_code_response(swift_details, branch_details)

    logger.info(f"SWIFT code {swift_code} is not a headquarter, returning single entry")
    return construct_swift_code_response(swift_details)


@router.get("/{swift_code}", response_model=SwiftCodeResponse)
def get_swift_code(swift_code: str, db: Session = Depends(yield_db)):
    """
    Endpoint to get bank details by SWIFT code.
    """
    return get_swift_code_details(swift_code, db)


def fetch_swift_codes_by_country(country_iso2: str, db: Session) -> list[SwiftCode]:
    """
    Fetch all SWIFT codes (headquarters and branches) for a given country.
    """
    logger.info(f"Fetching SWIFT codes for country ISO2: {country_iso2}")
    swift_codes = db.query(SwiftCode).filter(SwiftCode.country_iso2 == country_iso2).all()
    if not swift_codes:
        logger.warning(f"No SWIFT codes found for country ISO2: {country_iso2}")
        raise HTTPException(status_code=404, detail="No SWIFT codes found for this country")
    logger.info(f"Found {len(swift_codes)} SWIFT codes for country with ISO2: {country_iso2}")
    return swift_codes


def construct_country_swift_code_response(
    country_iso2: str, country_name: str, swift_codes: list
) -> CountrySwiftCodesResponse:
    """
    Construct the response with country details and associated SWIFT codes.
    """
    logger.info(f"Constructing response for country ISO2: {country_iso2}")
    return CountrySwiftCodesResponse(
        countryISO2=country_iso2,
        countryName=country_name,
        swiftCodes=[
            SwiftCodeEntry(
                address=code.address,
                bankName=code.name,
                countryISO2=country_iso2,
                isHeadquarter=code.is_headquarter,
                swiftCode=code.swift_code,
            )
            for code in swift_codes
        ],
    )


@router.get("/country/{country_iso2code}", response_model=CountrySwiftCodesResponse)
def get_swift_codes_by_country(country_iso2code: str, db: Session = Depends(yield_db)):
    """
    Endpoint to get all SWIFT codes for a specific country (both HQ and branches).
    """
    swift_codes = fetch_swift_codes_by_country(country_iso2code, db)
    country_name = swift_codes[0].country_name
    return construct_country_swift_code_response(country_iso2code, country_name, swift_codes)


@router.post("/", status_code=status.HTTP_201_CREATED)
def add_swift_code(swift_data: SwiftCodeCreate, db: Session = Depends(yield_db)):
    existing = db.query(SwiftCode).filter(SwiftCode.swift_code == swift_data.swiftCode).first()
    if existing:
        logger.warning(f"SWIFT code {swift_data.swiftCode} already exists in the database")
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

    logger.info(f"Adding SWIFT code {swift_data.swiftCode} to the database")

    db.add(new_entry)
    try:
        db.commit()
        db.refresh(new_entry)
        logger.info(f"SWIFT code {swift_data.swiftCode} added successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Error while adding SWIFT code {swift_data.swiftCode}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add SWIFT code to the database")

    return {"message": "SWIFT code added successfully", "swiftCode": new_entry.swift_code}


@router.delete("/{swift_code}", response_model=dict)
def delete_swift_code(swift_code: str, db: Session = Depends(yield_db)):
    entry_to_delete = db.query(SwiftCode).filter(SwiftCode.swift_code == swift_code).first()

    if not entry_to_delete:
        logger.warning(f"SWIFT code {swift_code} not found in the database.")
        raise HTTPException(status_code=404, detail="SWIFT code not found")

    db.delete(entry_to_delete)
    try:
        db.commit()
        logger.info(f"SWIFT code {swift_code} deleted successfully")
        return {"message": f"SWIFT code {swift_code} deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error while deleting SWIFT code {swift_code}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete SWIFT code from the database")
