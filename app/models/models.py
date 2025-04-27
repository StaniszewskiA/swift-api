from sqlalchemy import Column, String, Boolean
from .database import Base


class SwiftCode(Base):
    __tablename__ = "swift_codes"

    swift_code = Column(String, primary_key=True, index=True)
    address = Column(String, nullable=False)
    bank_name = Column(String, nullable=False)
    country_iso2 = Column(String(2), nullable=False)
    country_name = Column(String, nullable=False)
    is_headquarter = Column(Boolean, nullable=False)
