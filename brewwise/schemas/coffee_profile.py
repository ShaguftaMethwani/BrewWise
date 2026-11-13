from datetime import datetime, timezone
import uuid
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from brewwise.schemas.scan import ExtractedFieldCompact, CoffeeProfileDraftCompact


class ExtractedField(BaseModel):
    value: Optional[str] = None
    confidence: float = 0.0
    source: Literal["bag_text", "inferred", "user_override", "unknown"] = "bag_text"
    raw_text: Optional[str] = None

    @classmethod
    def from_compact(cls, compact: Optional[ExtractedFieldCompact], source: Literal["bag_text", "inferred", "user_override", "unknown"] = "bag_text") -> "ExtractedField":
        if compact is None:
            return cls(value=None, confidence=0.0, source="unknown")
        src = source if compact.v else "unknown"
        return cls(value=compact.v, confidence=compact.c, source=src, raw_text=None)


def _default_field() -> ExtractedField:
    return ExtractedField(value=None, confidence=0.0, source="unknown")


class CoffeeProfileDraft(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    brand: ExtractedField = Field(default_factory=_default_field)
    product_name: ExtractedField = Field(default_factory=_default_field)
    estate: ExtractedField = Field(default_factory=_default_field)
    country: ExtractedField = Field(default_factory=_default_field)
    region: ExtractedField = Field(default_factory=_default_field)
    varietal: ExtractedField = Field(default_factory=_default_field)
    process: ExtractedField = Field(default_factory=_default_field)
    roast_level: ExtractedField = Field(default_factory=_default_field)
    roast_date: ExtractedField = Field(default_factory=_default_field)
    tasting_notes: ExtractedField = Field(default_factory=_default_field)
    altitude: ExtractedField = Field(default_factory=_default_field)
    dose_recommendation: Optional[ExtractedField] = None
    additional_info: List[ExtractedField] = Field(default_factory=list)
    image_id: Optional[str] = None
    image_url: Optional[str] = None
    extraction_model: str = "gemini-2.5-flash"
    extraction_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_coffee_bag: bool = True
    rejection_reason: Optional[str] = None

    @classmethod
    def from_compact(
        cls,
        compact: CoffeeProfileDraftCompact,
        image_id: Optional[str] = None,
        image_url: Optional[str] = None,
        model: str = "gemini-2.5-flash"
    ) -> "CoffeeProfileDraft":
        return cls(
            id=str(uuid.uuid4()),
            brand=ExtractedField.from_compact(compact.brand),
            product_name=ExtractedField.from_compact(compact.name),
            estate=ExtractedField.from_compact(compact.estate),
            country=ExtractedField.from_compact(compact.country),
            region=ExtractedField.from_compact(compact.region),
            varietal=ExtractedField.from_compact(compact.varietal),
            process=ExtractedField.from_compact(compact.process),
            roast_level=ExtractedField.from_compact(compact.roast),
            roast_date=ExtractedField.from_compact(compact.roast_date),
            tasting_notes=ExtractedField.from_compact(compact.notes),
            altitude=ExtractedField.from_compact(compact.altitude),
            dose_recommendation=ExtractedField.from_compact(compact.dose) if compact.dose else None,
            additional_info=[ExtractedField.from_compact(item) for item in compact.extra],
            image_id=image_id,
            image_url=image_url,
            extraction_model=model,
            extraction_timestamp=datetime.now(timezone.utc),
            is_coffee_bag=compact.is_coffee_bag,
            rejection_reason=compact.rejection_reason
        )


class CoffeeProfileUpdate(BaseModel):
    brand: Optional[str] = None
    product_name: Optional[str] = None
    estate: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    varietal: Optional[str] = None
    process: Optional[str] = None
    roast_level: Optional[str] = None
    roast_date: Optional[str] = None
    tasting_notes: Optional[str] = None
    altitude: Optional[str] = None
