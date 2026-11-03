from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, JSON, Text
from brewwise.db.session import Base


class CoffeeProfileModel(Base):
    __tablename__ = "coffee_profiles"

    id = Column(String, primary_key=True, index=True)
    brand = Column(String, nullable=True, index=True)
    product_name = Column(String, nullable=True, index=True)
    country = Column(String, nullable=True)
    region = Column(String, nullable=True)
    estate = Column(String, nullable=True)
    varietal = Column(String, nullable=True)
    process = Column(String, nullable=True)
    roast_level = Column(String, nullable=True)
    roast_date = Column(String, nullable=True)
    tasting_notes = Column(Text, nullable=True)
    altitude = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    raw_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
