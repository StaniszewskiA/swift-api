from app.schemas.swift_code import SwiftCodeResponse
from fastapi import APIRouter, Depends, HTTPException
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
    return get_swift_code_details(swift_code, db)
