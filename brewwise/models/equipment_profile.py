import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from brewwise.db.session import Base


class UserEquipmentProfileModel(Base):
    __tablename__ = "user_equipment_profiles"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String, nullable=False, default="Default Setup")
    dripper = Column(String, nullable=False, default="Hario V60")
    grinder = Column(String, nullable=True)
    filter_type = Column(String, nullable=True, default="Paper")
    preferred_dose_g = Column(Float, default=15.0)
    preferred_ratio = Column(String, default="1:16")
    experience_level = Column(String, default="intermediate")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
