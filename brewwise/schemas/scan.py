from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ExtractedFieldCompact(BaseModel):
    v: Optional[str] = Field(default=None, description="Extracted value")
    c: float = Field(default=0.0, description="Confidence score between 0.0 and 1.0")


class CoffeeProfileDraftCompact(BaseModel):
    brand: ExtractedFieldCompact = Field(default_factory=ExtractedFieldCompact)
    name: ExtractedFieldCompact = Field(default_factory=ExtractedFieldCompact)
    estate: ExtractedFieldCompact = Field(default_factory=ExtractedFieldCompact)
    country: ExtractedFieldCompact = Field(default_factory=ExtractedFieldCompact)
    region: ExtractedFieldCompact = Field(default_factory=ExtractedFieldCompact)
    varietal: ExtractedFieldCompact = Field(default_factory=ExtractedFieldCompact)
    process: ExtractedFieldCompact = Field(default_factory=ExtractedFieldCompact)
    roast: ExtractedFieldCompact = Field(default_factory=ExtractedFieldCompact)
    roast_date: ExtractedFieldCompact = Field(default_factory=ExtractedFieldCompact)
    notes: ExtractedFieldCompact = Field(default_factory=ExtractedFieldCompact)
    altitude: ExtractedFieldCompact = Field(default_factory=ExtractedFieldCompact)
    dose: Optional[ExtractedFieldCompact] = None
    extra: List[ExtractedFieldCompact] = Field(default_factory=list)
    is_coffee_bag: bool = Field(default=True, description="False if uploaded image is not coffee")
    rejection_reason: Optional[str] = Field(default=None, description="Explanation if not a coffee bag")
