from sqlalchemy import Column, String, Boolean
from app.core.database import Base


class SwiftCode(Base):
    __tablename__ = "swift_codes"

    swift_code = Column(String, primary_key=True, index=True)
    bank_name = Column(String)
    country_iso2 = Column(String, index=True)
    country_name = Column(String)
    is_headquarter = Column(Boolean, default=False)
    headquarters_code = Column(String)
