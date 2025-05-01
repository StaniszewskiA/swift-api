from sqlalchemy import Column, String, Boolean
from app.core.database import AsyncBase


class SwiftCode(AsyncBase):
    __tablename__ = "swift_codes"

    swift_code = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True)
    address = Column(String, nullable=True)
    country_iso2 = Column(String, index=True, nullable=True)
    country_name = Column(String, nullable=True)
    is_headquarter = Column(Boolean, default=False)
    headquarters_code = Column(String, nullable=True)
