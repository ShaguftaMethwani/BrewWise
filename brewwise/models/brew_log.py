import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey, Text
from brewwise.db.session import Base


class BrewLogModel(Base):
    __tablename__ = "brew_logs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    recipe_id = Column(String, ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True, index=True)
    coffee_profile_id = Column(String, ForeignKey("coffee_profiles.id", ondelete="SET NULL"), nullable=True, index=True)

    brewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    dripper = Column(String, nullable=False, default="Hario V60")
    grinder = Column(String, nullable=True)

    # Actual parameters used
    actual_dose_g = Column(Float, nullable=False, default=15.0)
    actual_water_g = Column(Float, nullable=False, default=240.0)
    actual_grind_setting = Column(String, nullable=True)
    actual_temp_c = Column(Integer, nullable=False, default=93)
    actual_brew_time_seconds = Column(Integer, nullable=False, default=180)

    # Sensory feedback (1 - 5)
    sourness = Column(Integer, default=3)
    bitterness = Column(Integer, default=3)
    sweetness = Column(Integer, default=3)
    body = Column(Integer, default=3)
    overall_satisfaction = Column(Integer, default=4)
    drawdown_speed = Column(String, default="normal")  # fast, normal, slow, stalled

    flavour_notes = Column(Text, nullable=True)
    adjustments = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
