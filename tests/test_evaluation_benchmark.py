import json
from pathlib import Path
import pytest

from brewwise.services.identity.normaliser import (
    normalise_roaster_name,
    normalise_process_method,
    normalise_roast_level
)
from brewwise.services.synthesis.recipe_generator import RecipeGenerator
from brewwise.services.retrieval.query_builder import QueryBuilder
from brewwise.services.retrieval.relevance import MatchClassifier
from brewwise.schemas.coffee_profile import CoffeeProfileDraft, ExtractedField


def load_eval_dataset():
    data_path = Path(__file__).parent.parent / "data" / "evaluation_dataset.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_eval_dataset_size_and_diversity():
    items = load_eval_dataset()
    assert len(items) == 30

    origins = {item["country"] for item in items}
    assert len(origins) >= 8  # Broad multi-continent coverage

    processes = {item["process"] for item in items}
    assert "Washed" in processes
    assert "Natural" in processes
    assert any("Anaerobic" in p for p in processes)

    roasts = {item["roast_level"] for item in items}
    assert "Light" in roasts
    assert "Medium" in roasts


def test_eval_dataset_normalization():
    items = load_eval_dataset()
    for item in items:
        norm_roaster = normalise_roaster_name(item["brand"])
        assert norm_roaster is not None
        assert len(norm_roaster) > 0

        norm_proc = normalise_process_method(item["process"])
        assert norm_proc is not None
        assert any(p in norm_proc for p in ["wash", "nat", "honey", "anaerob", "macerat", "shock", "pulp", "other"])

        norm_roast = normalise_roast_level(item["roast_level"])
        assert norm_roast in ["light", "medium_light", "medium", "medium_dark", "dark"]


def test_eval_dataset_recipe_arithmetic_soundness():
    """Verify that simulated recipes for all 30 eval coffees satisfy 100% mathematical validity."""
    items = load_eval_dataset()
    for item in items:
        # Create draft profile
        draft = CoffeeProfileDraft(
            id=item["id"],
            brand=ExtractedField(value=item["brand"], confidence=0.95, source="bag_text"),
            product_name=ExtractedField(value=item["product_name"], confidence=0.95, source="bag_text"),
            country=ExtractedField(value=item["country"], confidence=0.9, source="bag_text"),
            process=ExtractedField(value=item["process"], confidence=0.9, source="bag_text"),
            roast_level=ExtractedField(value=item["roast_level"], confidence=0.9, source="bag_text"),
            varietal=ExtractedField(value=item.get("varietal"), confidence=0.85, source="bag_text")
        )

        # Baseline generation using deterministic fallback
        recipe = RecipeGenerator.generate_fallback_baseline(draft, dripper=item.get("target_dripper", "Hario V60"))

        # Strict arithmetic assertions
        assert recipe.dose_g > 0
        assert recipe.water_g > 0
        assert recipe.water_temperature_c >= 80 and recipe.water_temperature_c <= 99
        assert len(recipe.pour_schedule) >= 2

        # Sum of pours equals total water
        total_pour_water = sum(p.water_g for p in recipe.pour_schedule)
        assert round(total_pour_water, 1) == round(recipe.water_g, 1)

        # Final cumulative water matches total water
        assert round(recipe.pour_schedule[-1].cumulative_water_g, 1) == round(recipe.water_g, 1)


def test_eval_dataset_query_construction():
    """Verify query builder constructs valid hybrid keyword + semantic queries for all eval items."""
    items = load_eval_dataset()
    for item in items:
        draft = CoffeeProfileDraft(
            id=item["id"],
            brand=ExtractedField(value=item["brand"], confidence=0.95, source="bag_text"),
            product_name=ExtractedField(value=item["product_name"], confidence=0.95, source="bag_text"),
            country=ExtractedField(value=item["country"], confidence=0.9, source="bag_text"),
            process=ExtractedField(value=item["process"], confidence=0.9, source="bag_text"),
            roast_level=ExtractedField(value=item["roast_level"], confidence=0.9, source="bag_text")
        )
        queries = QueryBuilder.build_queries(draft, dripper=item.get("target_dripper", "Hario V60"))
        assert len(queries) >= 2
        assert any(item["brand"] in q or item["product_name"] in q or item["country"] in q for q in queries)
