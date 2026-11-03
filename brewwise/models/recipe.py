from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey
from brewwise.db.session import Base


class RecipeModel(Base):
    __tablename__ = "recipes"

    id = Column(String, primary_key=True, index=True)
    coffee_profile_id = Column(String, ForeignKey("coffee_profiles.id"), nullable=False, index=True)
    source_type = Column(String, default="ai_generated")
    generation_model = Column(String, nullable=True)

    dripper = Column(String, default="Hario V60")
    grinder = Column(String, nullable=True)
    filter_type = Column(String, nullable=True)

    dose_g = Column(Float, nullable=False)
    water_g = Column(Float, nullable=False)
    ratio = Column(String, nullable=False)
    water_temperature_c = Column(Integer, nullable=False)
    grind_description = Column(String, nullable=False)
    grind_setting = Column(String, nullable=True)

    filter_prep = Column(String, nullable=True)
    bloom_water_g = Column(Float, nullable=False)
    bloom_time_seconds = Column(Integer, nullable=False)
    target_brew_time_seconds = Column(Integer, nullable=False)

    pour_schedule = Column(JSON, nullable=False)
    step_by_step_instructions = Column(JSON, nullable=False)
    expected_flavour = Column(String, nullable=True)
    explanation = Column(JSON, nullable=True)
    troubleshooting = Column(JSON, nullable=True)
    limitations = Column(JSON, nullable=True)

    confidence = Column(Float, default=0.85)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
