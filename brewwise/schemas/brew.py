from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field


class AdjustmentRecommendation(BaseModel):
    diagnosis: str
    primary_adjustment: str
    secondary_adjustment: Optional[str] = None
    suggested_parameters: Dict[str, Any] = Field(default_factory=dict)
    rationale: str


class BrewLogCreate(BaseModel):
    recipe_id: Optional[str] = None
    coffee_profile_id: Optional[str] = None
    dripper: str = "Hario V60"
    grinder: Optional[str] = None
    actual_dose_g: float = 15.0
    actual_water_g: float = 240.0
    actual_grind_setting: Optional[str] = None
    actual_temp_c: int = 93
    actual_brew_time_seconds: int = 180

    sourness: int = Field(default=3, ge=1, le=5, description="1 = Flat/Mundane, 5 = Very Sour/Tart")
    bitterness: int = Field(default=3, ge=1, le=5, description="1 = No Bitterness, 5 = Harsh/Astringent")
    sweetness: int = Field(default=3, ge=1, le=5, description="1 = No Sweetness, 5 = Syrupy Sweet")
    body: int = Field(default=3, ge=1, le=5, description="1 = Watery/Tea-like, 5 = Heavy/Thick")
    overall_satisfaction: int = Field(default=4, ge=1, le=5, description="1 = Poor, 5 = Exceptional Cup")

    drawdown_speed: Literal["fast", "normal", "slow", "stalled"] = "normal"
    flavour_notes: Optional[str] = None


class BrewLogFeedbackUpdate(BaseModel):
    sourness: Optional[int] = Field(default=None, ge=1, le=5)
    bitterness: Optional[int] = Field(default=None, ge=1, le=5)
    sweetness: Optional[int] = Field(default=None, ge=1, le=5)
    body: Optional[int] = Field(default=None, ge=1, le=5)
    overall_satisfaction: Optional[int] = Field(default=None, ge=1, le=5)
    drawdown_speed: Optional[Literal["fast", "normal", "slow", "stalled"]] = None
    flavour_notes: Optional[str] = None


class BrewLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    recipe_id: Optional[str] = None
    coffee_profile_id: Optional[str] = None
    brewed_at: datetime
    dripper: str
    grinder: Optional[str] = None
    actual_dose_g: float
    actual_water_g: float
    actual_grind_setting: Optional[str] = None
    actual_temp_c: int
    actual_brew_time_seconds: int

    sourness: int
    bitterness: int
    sweetness: int
    body: int
    overall_satisfaction: int
    drawdown_speed: str
    flavour_notes: Optional[str] = None
    adjustments: Optional[AdjustmentRecommendation] = None
    created_at: datetime
