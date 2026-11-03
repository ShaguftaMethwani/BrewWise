import pytest
from brewwise.schemas.scan import ExtractedFieldCompact, CoffeeProfileDraftCompact
from brewwise.schemas.coffee_profile import CoffeeProfileDraft, ExtractedField


def test_compact_inflation():
    compact = CoffeeProfileDraftCompact(
        brand=ExtractedFieldCompact(v="Subko", c=0.98),
        name=ExtractedFieldCompact(v="Project Sankalp", c=0.92),
        estate=ExtractedFieldCompact(v="Ratnagiri Estate", c=0.88),
        country=ExtractedFieldCompact(v="India", c=0.99),
        region=ExtractedFieldCompact(v="Karnataka", c=0.90),
        varietal=ExtractedFieldCompact(v="Catimor", c=0.85),
        process=ExtractedFieldCompact(v="Natural", c=0.95),
        roast=ExtractedFieldCompact(v="Light Roast", c=0.90),
        roast_date=ExtractedFieldCompact(v="2026-10-20", c=0.99),
        notes=ExtractedFieldCompact(v="Mango, Passion Fruit, Hibiscus", c=0.88),
        altitude=ExtractedFieldCompact(v="1400 masl", c=0.80),
        dose=ExtractedFieldCompact(v="15g", c=0.75),
        extra=[],
        is_coffee_bag=True
    )

    draft = CoffeeProfileDraft.from_compact(
        compact=compact,
        image_id="img_123.jpg",
        image_url="/uploads/img_123.jpg",
        model="gemini-2.5-flash"
    )

    assert draft.brand.value == "Subko"
    assert draft.brand.confidence == 0.98
    assert draft.brand.source == "bag_text"
    assert draft.product_name.value == "Project Sankalp"
    assert draft.is_coffee_bag is True
    assert draft.image_id == "img_123.jpg"
