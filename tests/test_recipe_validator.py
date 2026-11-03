import pytest
from brewwise.schemas.recipe import (
    RecipeGenerationOutput,
    PourStep,
    RecipeExplanation,
    TroubleshootingTip
)
from brewwise.services.synthesis.validator import RecipeValidator


def test_recipe_validator_valid():
    output = RecipeGenerationOutput(
        dose_g=15.0,
        water_g=240.0,
        ratio="1:16",
        water_temperature_c=93,
        grind_description="Medium fine",
        bloom_water_g=45.0,
        bloom_time_seconds=45,
        pour_schedule=[
            PourStep(step_number=1, water_g=45.0, cumulative_water_g=45.0, start_time_seconds=0, duration_seconds=15, technique="Spiral"),
            PourStep(step_number=2, water_g=95.0, cumulative_water_g=140.0, start_time_seconds=45, duration_seconds=20, technique="Spiral"),
            PourStep(step_number=3, water_g=100.0, cumulative_water_g=240.0, start_time_seconds=90, duration_seconds=20, technique="Center"),
        ],
        target_brew_time_seconds=180,
        step_by_step_instructions=["Step 1", "Step 2"],
        expected_flavour="Balanced fruit sweetness",
        explanation=RecipeExplanation(reasoning_summary="Tested recipe"),
        troubleshooting=[TroubleshootingTip(symptom="Sour", likely_cause="Fast flow", adjustment="Grind finer")],
        limitations=[]
    )
    is_valid, errors = RecipeValidator.validate(output)
    assert is_valid is True
    assert len(errors) == 0


def test_recipe_validator_catches_pour_mismatch():
    output = RecipeGenerationOutput(
        dose_g=15.0,
        water_g=240.0,
        ratio="1:16",
        water_temperature_c=93,
        grind_description="Medium fine",
        bloom_water_g=45.0,
        bloom_time_seconds=45,
        pour_schedule=[
            # Pours sum to 200g instead of 240g
            PourStep(step_number=1, water_g=45.0, cumulative_water_g=45.0, start_time_seconds=0, duration_seconds=15, technique="Spiral"),
            PourStep(step_number=2, water_g=155.0, cumulative_water_g=200.0, start_time_seconds=45, duration_seconds=20, technique="Spiral"),
        ],
        target_brew_time_seconds=180,
        step_by_step_instructions=["Step 1"],
        expected_flavour="Test",
        explanation=RecipeExplanation(reasoning_summary="Test"),
    )
    is_valid, errors = RecipeValidator.validate(output)
    assert is_valid is False
    assert any("does not equal total water" in e for e in errors)


def test_recipe_validator_catches_bad_temp():
    output = RecipeGenerationOutput(
        dose_g=15.0,
        water_g=240.0,
        ratio="1:16",
        water_temperature_c=75,  # Too cold (<85)
        grind_description="Medium fine",
        bloom_water_g=45.0,
        bloom_time_seconds=45,
        pour_schedule=[
            PourStep(step_number=1, water_g=240.0, cumulative_water_g=240.0, start_time_seconds=0, duration_seconds=30, technique="Single"),
        ],
        target_brew_time_seconds=180,
        step_by_step_instructions=["Step 1"],
        expected_flavour="Test",
        explanation=RecipeExplanation(reasoning_summary="Test"),
    )
    is_valid, errors = RecipeValidator.validate(output)
    assert is_valid is False
    assert any("temperature" in e for e in errors)
