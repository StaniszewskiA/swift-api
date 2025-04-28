from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import yield_db
from app.models.models import SwiftCode

router = APIRouter(prefix="/v1/swift-codes", tags=["Swift Codes"])


def get_swift_code_details(swift_code: str, db: Session) -> dict:
    swift_details = db.query(SwiftCode).filter(SwiftCode.swift_code == swift_code).first()
    if not swift_details:
        raise HTTPException(status_code=404, detail="SWIFT code not found")

    if swift_details.is_headquarter:
        branches = db.query(SwiftCode).filter(SwiftCode.headquarters_code == swift_code).all()
        branch_details = [
            {
                # "address": TODO
                "bankName": branch.name,
                "countryISO2": branch.country_iso2,
                "countryName": branch.country_name,
                "isHeadquarter": branch.is_headquarter,
                "swiftCode": branch.swift_code,
            }
            for branch in branches
        ]
        return {
            # "address": TODO
            "bankName": swift_details.name,
            "countryISO2": swift_details.country_iso2,
            "countryName": swift_details.country_name,
            "isHeadquarter": swift_details.is_headquarter,
            "swiftCode": swift_details.swift_code,
            "branches": branch_details,
        }

    return {
        # "address": TODO
        "bankName": swift_details.name,
        "countryISO2": swift_details.country_iso2,
        "countryName": swift_details.country_name,
        "isHeadquarter": swift_details.is_headquarter,
        "swiftCode": swift_details.swift_code,
    }


@router.get("/{swift_code}", response_model=dict)
def get_swift_code(swift_code: str, db: Session = Depends(yield_db)):
    return get_swift_code_details(swift_code, db)
