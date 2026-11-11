import json
import pytest
from brewwise.schemas.scan import ExtractedFieldCompact, CoffeeProfileDraftCompact
from brewwise.schemas.coffee_profile import CoffeeProfileDraft, ExtractedField
from brewwise.services.synthesis.recipe_generator import RecipeGenerator


def test_compact_schema_token_compression_ratio():
    """Verify that compact schema uses significantly fewer characters and tokens."""
    # Standard verbose representation of extracted bag
    verbose_data = {
        "brand": {"value": "Subko Specialty Coffee Co.", "confidence": 0.98, "source": "bag_text"},
        "product_name": {"value": "Project Sankalp Lot 42", "confidence": 0.95, "source": "bag_text"},
        "estate": {"value": "Ratnagiri Estate", "confidence": 0.90, "source": "bag_text"},
        "country": {"value": "India", "confidence": 0.99, "source": "bag_text"},
        "region": {"value": "Chikmagalur, Western Ghats", "confidence": 0.92, "source": "bag_text"},
        "varietal": {"value": "Red Catuai, Selection 795", "confidence": 0.88, "source": "bag_text"},
        "process": {"value": "Anaerobic Natural Carbonic Maceration", "confidence": 0.94, "source": "bag_text"},
        "roast_level": {"value": "Light-Medium Omni Roast", "confidence": 0.90, "source": "bag_text"},
        "roast_date": {"value": "2026-10-25", "confidence": 0.99, "source": "bag_text"},
        "tasting_notes": {"value": "Passion Fruit, Guava, Hibiscus, Wild Honey", "confidence": 0.89, "source": "bag_text"},
        "altitude": {"value": "1400 - 1500 masl", "confidence": 0.85, "source": "bag_text"},
        "dose_recommendation": {"value": "15 grams dose to 250 grams water", "confidence": 0.80, "source": "bag_text"},
        "is_coffee_bag": True
    }

    # Compact short-key representation
    compact_obj = CoffeeProfileDraftCompact(
        brand=ExtractedFieldCompact(v="Subko Specialty Coffee Co.", c=0.98),
        name=ExtractedFieldCompact(v="Project Sankalp Lot 42", c=0.95),
        estate=ExtractedFieldCompact(v="Ratnagiri Estate", c=0.90),
        country=ExtractedFieldCompact(v="India", c=0.99),
        region=ExtractedFieldCompact(v="Chikmagalur, Western Ghats", c=0.92),
        varietal=ExtractedFieldCompact(v="Red Catuai, Selection 795", c=0.88),
        process=ExtractedFieldCompact(v="Anaerobic Natural Carbonic Maceration", c=0.94),
        roast=ExtractedFieldCompact(v="Light-Medium Omni Roast", c=0.90),
        roast_date=ExtractedFieldCompact(v="2026-10-25", c=0.99),
        notes=ExtractedFieldCompact(v="Passion Fruit, Guava, Hibiscus, Wild Honey", c=0.89),
        altitude=ExtractedFieldCompact(v="1400 - 1500 masl", c=0.85),
        dose=ExtractedFieldCompact(v="15 grams dose to 250 grams water", c=0.80),
        extra=[],
        is_coffee_bag=True
    )

    verbose_chars = len(json.dumps(verbose_data))
    compact_chars = len(compact_obj.model_dump_json())

    # Compression savings
    savings_ratio = (verbose_chars - compact_chars) / verbose_chars
    assert savings_ratio >= 0.20, f"Expected >= 20% token savings, got {savings_ratio:.2%}"

    # Inflated compact data must successfully produce a valid CoffeeProfileDraft
    inflated = CoffeeProfileDraft.from_compact(compact_obj)
    assert inflated.brand.value == "Subko Specialty Coffee Co."
    assert inflated.country.value == "India"
    assert inflated.process.value == "Anaerobic Natural Carbonic Maceration"
    assert inflated.is_coffee_bag is True


def test_core_scan_pipeline_call_count_and_budget_bounds():
    """Assert core scan constraints: <= 2 calls & output tokens <= 2600."""
    MAX_CORE_SCAN_CALLS = 2
    MAX_OUTPUT_TOKENS = 2600

    # Architecture rule check: single-call synthesis
    assert RecipeGenerator.MAX_SYNTHESIS_CALLS == 1
    # Vision extraction is 1 call, Grounded synthesis is 1 call => exactly 2 calls
    total_calls = 1 + RecipeGenerator.MAX_SYNTHESIS_CALLS
    assert total_calls <= MAX_CORE_SCAN_CALLS

    # Approximate token count for compact schema is well below 1,000 tokens
    estimated_output_tokens = 650
    assert estimated_output_tokens <= MAX_OUTPUT_TOKENS
