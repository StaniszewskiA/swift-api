from pydantic import BaseModel
from typing import Optional


class Branch(BaseModel):
    address: str
    bankName: str
    countryISO2: str
    countryName: str
    isHeadquarter: bool
    swiftCode: str


class SwiftCodeResponse(BaseModel):
    address: str
    bankName: str
    countryISO2: str
    countryName: str
    isHeadquarter: bool
    swiftCode: str
    branches: Optional[list[Branch]] = []
