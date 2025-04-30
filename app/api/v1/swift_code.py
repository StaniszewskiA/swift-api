from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import yield_db
from app.schemas.swift_code_schema import SwiftCodeCreate, SwiftCodeResponse, CountrySwiftCodesResponse
from app.crud import swift_code_crud

router = APIRouter(prefix="/v1/swift-codes", tags=["Swift Codes"])


@router.get("/{swift_code}", response_model=SwiftCodeResponse)
def get_swift_code(swift_code: str, db: Session = Depends(yield_db)):
    return swift_code_crud.get_swift_code_details(swift_code, db)


@router.get("/country/{country_iso2code}", response_model=CountrySwiftCodesResponse)
def get_swift_codes_by_country(country_iso2code: str, db: Session = Depends(yield_db)):
    swift_codes = swift_code_crud.fetch_swift_codes_by_country(country_iso2code, db)
    country_name = swift_codes[0].country_name
    return swift_code_crud.construct_country_swift_code_response(country_iso2code, country_name, swift_codes)


@router.post("/", status_code=status.HTTP_201_CREATED)
def add_swift_code(swift_data: SwiftCodeCreate, db: Session = Depends(yield_db)):
    response = swift_code_crud.add_swift_code(swift_data, db)
    return response


@router.delete("/{swift_code}", response_model=dict)
def delete_swift_code(swift_code: str, db: Session = Depends(yield_db)):
    response = swift_code_crud.delete_swift_code(swift_code, db)
    return response
