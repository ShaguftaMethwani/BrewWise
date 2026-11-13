"""Tests for the 'never fabricate' guarantees: identity matching, live extraction, labelling, validation."""
import pytest

from brewwise.models.recipe_source import RecipeSourceModel
from brewwise.schemas.coffee_profile import CoffeeProfileDraft, ExtractedField
from brewwise.schemas.recipe import RecipeGenerateRequest
from brewwise.services.discovery.recipe_extractor import (
    LiveRecipeExtractor,
    LLMPageRecipe,
    DiscoveredRecipeBatch,
    focus_recipe_excerpt,
)
from brewwise.services.ingestion.parser import extract_observed_parameters
from brewwise.services.ingestion.scrapers.base import RawContent
from brewwise.services.retrieval.evidence_evaluator import EvidenceEvaluator
from brewwise.services.retrieval.relevance import MatchClassifier, MatchClassification
from brewwise.services.synthesis.recipe_generator import RecipeGenerator, generate_baseline_recipe
from brewwise.services.synthesis.validator import RecipeValidator
from brewwise.api.v1.scan import sniff_image_type


def _profile(**fields) -> CoffeeProfileDraft:
    return CoffeeProfileDraft(
        id="p1",
        **{k: ExtractedField(value=v, confidence=0.9, source="bag_text") for k, v in fields.items()},
    )


def _source(meta, title="V60 pour-over recipe", method="curated", recipe=None) -> RecipeSourceModel:
    return RecipeSourceModel(
        id="s1",
        url="https://example.com/recipe",
        title=title,
        raw_content="Pour-over recipe on Hario V60",
        content_hash="h",
        extraction_method=method,
        coffee_metadata=meta,
        extracted_recipe=recipe or {"dripper": "Hario V60", "dose_g": 15.0, "water_g": 240.0, "ratio": "1:16"},
    )


ATTIKAN = dict(brand="Blue Tokai", estate="Attikan Estate", product_name="Attikan Estate", country="India", process="washed")


# --- Identity matching -------------------------------------------------------

def test_source_without_identity_metadata_is_never_an_identity_match():
    """A page with no brand/estate metadata must not be labelled 'identical estate & roaster'."""
    match = MatchClassifier.score_and_classify(_source({"country": "India"}), _profile(**ATTIKAN))
    if match is not None:
        assert match.match_type not in (MatchClassification.EXACT, MatchClassification.STRONG)
        assert not any("estate" in r.lower() for r in match.match_reasons)


def test_same_estate_different_process_is_related_not_exact():
    meta = {"brand": "Blue Tokai", "estate": "Attikan Estate", "country": "India", "process": "Natural"}
    match = MatchClassifier.score_and_classify(_source(meta), _profile(**ATTIKAN))
    assert match is not None
    assert match.match_type == MatchClassification.RELATED
    assert any("different lot" in r.lower() for r in match.match_reasons)


def test_same_estate_different_roaster_is_related_not_exact():
    meta = {"brand": "Third Wave Roasters", "estate": "Attikan Estate", "country": "India", "process": "Washed"}
    match = MatchClassifier.score_and_classify(_source(meta), _profile(**ATTIKAN))
    assert match is not None
    assert match.match_type == MatchClassification.RELATED


def test_same_coffee_with_naming_variation_is_exact():
    meta = {"brand": "Blue Tokai Coffee Roasters", "estate": "Attikan Estate", "country": "India", "process": "Fully Washed"}
    match = MatchClassifier.score_and_classify(_source(meta), _profile(**ATTIKAN))
    assert match is not None
    assert match.match_type == MatchClassification.EXACT


# --- Live extraction ---------------------------------------------------------

def test_observed_parameters_are_not_defaulted():
    assert extract_observed_parameters("Our V60 story: we love the bloom and a good ratio.") == {"dripper": "Hario V60"}
    found = extract_observed_parameters("Use 18g of coffee and 300g water at 205°F, medium-fine grind.")
    assert found["dose_g"] == 18.0
    assert found["water_g"] == 300.0
    assert found["water_temperature_c"] == 96
    assert found["ratio"] == "1:16.7"
    assert found["grind_description"] == "Medium-fine"


@pytest.mark.asyncio
async def test_page_mentioning_brewing_without_quantities_yields_no_recipe():
    page = RawContent(
        url="https://roaster.example/attikan",
        title="Attikan Estate",
        content="A lovely washed coffee. Great as a pour-over on the V60 - mind your bloom and ratio.",
    )
    assert await LiveRecipeExtractor().extract_batch([page]) == []


class _FakeLLM:
    def __init__(self, batch):
        self.batch = batch

    async def generate_structured(self, prompt, response_schema, system_instruction=None, model=None):
        return self.batch

    async def generate_text(self, *a, **k):
        return ""


@pytest.mark.asyncio
async def test_llm_extraction_with_numbers_absent_from_page_is_rejected():
    page = RawContent(
        url="https://roaster.example/guide",
        title="Guide",
        content="Kalita pour-over notes: we enjoy this coffee in the morning. No quantities given.",
    )
    hallucinated = DiscoveredRecipeBatch(recipes=[
        LLMPageRecipe(page_index=0, has_recipe=True, dose_g=15, water_g=250, water_temperature_c=93),
        LLMPageRecipe(page_index=7, has_recipe=True, dose_g=15, water_g=250),  # page that was never fetched
    ])
    extractor = LiveRecipeExtractor(llm_provider=_FakeLLM(hallucinated))
    assert await extractor.extract_batch([page]) == []


@pytest.mark.asyncio
async def test_llm_extraction_grounded_in_page_is_kept_with_unstated_fields_left_empty():
    page = RawContent(
        url="https://roaster.example/attikan-v60",
        title="Attikan V60",
        content="Attikan Estate V60 pour-over: 15g coffee, 250g water. Bloom 30 seconds.",
    )
    batch = DiscoveredRecipeBatch(recipes=[
        LLMPageRecipe(page_index=0, has_recipe=True, dripper="Hario V60", dose_g=15, water_g=250,
                      water_temperature_c=93, coffee_estate="Attikan Estate"),
    ])
    recipes = await LiveRecipeExtractor(llm_provider=_FakeLLM(batch)).extract_batch([page])
    assert len(recipes) == 1
    assert recipes[0].url == page.url
    assert recipes[0].water_temperature_c is None  # 93 is not on the page
    assert recipes[0].coffee_metadata == {"estate": "Attikan Estate"}


def test_focus_excerpt_finds_recipe_after_long_intro():
    content = "intro " * 800 + "Recipe: Dose 15g, water 240g." + " outro" * 400
    excerpt = focus_recipe_excerpt(content, max_chars=600)
    assert "Dose 15g" in excerpt and len(excerpt) <= 600


# --- Recipe generation -------------------------------------------------------

def test_baseline_states_unknowns_as_assumptions_and_covers_troubleshooting():
    out = generate_baseline_recipe(_profile(brand="Some Roaster"), dripper="Kalita Wave", dose_g=20, target_strength="strong")
    valid, errors = RecipeValidator.validate(out)
    assert valid, errors
    assert out.ratio == "1:15" and out.water_g == 300.0
    assert any("roast level is not stated" in a.lower() for a in out.explanation.assumptions)
    assert "washed" not in out.explanation.reasoning_summary.lower()
    assert out.expected_flavour.lower().startswith("prediction")
    symptoms = " ".join(t.symptom.lower() for t in out.troubleshooting)
    assert all(k in symptoms for k in ("sour", "bitter", "weak", "slow"))
    assert len(out.pour_schedule) == 4  # flat-bottom: bloom + 3 pulses


@pytest.mark.asyncio
async def test_no_llm_no_evidence_is_labelled_rule_based_with_unknown_grinder_caveat():
    request = RecipeGenerateRequest(coffee_profile_id="p1", grinder="Mystery Grinder 3000")
    evidence = EvidenceEvaluator.evaluate([], discovery_status="disabled")
    recipe = await RecipeGenerator().generate(_profile(roast_level="light"), request, evidence=evidence)
    assert recipe.source_type == "curated_baseline"
    assert recipe.generation_model == "baseline-rule-engine"
    assert recipe.source_recipes == []
    assert recipe.grind_setting is None
    assert any("Mystery Grinder 3000" in l for l in recipe.limitations)
    assert recipe.confidence <= 0.6


@pytest.mark.asyncio
async def test_fallback_with_exact_evidence_uses_source_parameters():
    profile = _profile(**ATTIKAN)
    meta = {"brand": "Blue Tokai", "estate": "Attikan Estate", "country": "India", "process": "Washed"}
    source = _source(meta, recipe={"dripper": "Hario V60", "dose_g": 16.0, "water_g": 240.0, "ratio": "1:15", "water_temperature_c": 90})
    evidence = EvidenceEvaluator.evaluate([MatchClassifier.score_and_classify(source, profile)])
    recipe = await RecipeGenerator().generate(profile, RecipeGenerateRequest(coffee_profile_id="p1", dose_preference_g=20), evidence=evidence)
    assert recipe.source_type == "exact_match"
    assert recipe.ratio == "1:15" and recipe.water_g == 300.0 and recipe.water_temperature_c == 90
    assert [s.url for s in recipe.source_recipes] == ["https://example.com/recipe"]


def test_validator_rejects_impossible_timing():
    out = generate_baseline_recipe(_profile(roast_level="medium"))
    out.pour_schedule[-1].start_time_seconds = out.target_brew_time_seconds + 30
    valid, errors = RecipeValidator.validate(out)
    assert not valid and any("target brew time" in e for e in errors)


# --- Upload validation -------------------------------------------------------

def test_image_type_is_sniffed_from_content():
    assert sniff_image_type(b"\xff\xd8\xff\xe0" + b"0" * 10) == "image/jpeg"
    assert sniff_image_type(b"\x89PNG\r\n\x1a\n" + b"0" * 10) == "image/png"
    assert sniff_image_type(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"
    assert sniff_image_type(b"<html>not an image</html>") is None
