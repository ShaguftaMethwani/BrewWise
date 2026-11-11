import pytest
from brewwise.schemas.coffee_profile import CoffeeProfileDraft, ExtractedField
from brewwise.providers.embeddings.gemini_embed import GeminiEmbeddingProvider, generate_deterministic_embedding
from brewwise.services.retrieval.hybrid_retriever import cosine_similarity
from brewwise.services.retrieval.query_builder import QueryBuilder
from brewwise.services.retrieval.relevance import MatchClassifier, MatchClassification
from brewwise.services.retrieval.evidence_evaluator import EvidenceEvaluator
from brewwise.services.synthesis.provenance_verifier import ProvenanceVerifier
from brewwise.schemas.recipe import PersonalisedRecipe, RecipeExplanation, PourStep, SourceReference
from brewwise.models.recipe_source import RecipeSourceModel
from brewwise.services.ingestion.deduplicator import Deduplicator
from brewwise.services.ingestion.parser import RecipeParser


def test_embedding_dimensions_and_cosine():
    v1 = generate_deterministic_embedding("Ethiopian washed yirgacheffe floral", dim=768)
    v2 = generate_deterministic_embedding("Ethiopian washed yirgacheffe citrus peach", dim=768)
    v3 = generate_deterministic_embedding("Dark roast sumatra earthy tobacco", dim=768)

    assert len(v1) == 768
    assert len(v2) == 768
    assert len(v3) == 768

    # Similar coffees should have higher similarity than completely dissimilar coffees
    sim_12 = cosine_similarity(v1, v2)
    sim_13 = cosine_similarity(v1, v3)
    assert sim_12 > sim_13


def test_query_builder():
    draft = CoffeeProfileDraft(
        id="test-123",
        brand=ExtractedField(value="Blue Tokai Coffee Roasters", confidence=0.9),
        product_name=ExtractedField(value="Attikan Estate", confidence=0.9),
        estate=ExtractedField(value="Attikan Estate", confidence=0.9),
        country=ExtractedField(value="India", confidence=0.9),
        region=ExtractedField(value="Biligirirangana Hills", confidence=0.9),
        process=ExtractedField(value="Washed", confidence=0.9),
        roast_level=ExtractedField(value="Medium-Dark", confidence=0.9),
        varietal=ExtractedField(value="SLN 9", confidence=0.9),
        tasting_notes=ExtractedField(value="Dark chocolate, fig", confidence=0.9),
        altitude=ExtractedField(value="1350m", confidence=0.8),
    )

    queries = QueryBuilder.build_queries(draft, dripper="Hario V60")
    assert len(queries) >= 3
    # Exact query check
    assert any("Blue Tokai Coffee Roasters Attikan Estate" in q for q in queries)
    # Equipment query check
    assert any("Hario V60" in q for q in queries)


def test_match_classifier_exact_vs_related():
    draft = CoffeeProfileDraft(
        id="test-123",
        brand=ExtractedField(value="Blue Tokai Coffee Roasters", confidence=0.9),
        product_name=ExtractedField(value="Attikan Estate", confidence=0.9),
        estate=ExtractedField(value="Attikan Estate", confidence=0.9),
        country=ExtractedField(value="India", confidence=0.9),
        region=ExtractedField(value="Biligirirangana Hills", confidence=0.9),
        process=ExtractedField(value="Washed", confidence=0.9),
        roast_level=ExtractedField(value="Medium-Dark", confidence=0.9),
        varietal=ExtractedField(value="SLN 9", confidence=0.9),
        tasting_notes=ExtractedField(value="Dark chocolate, fig", confidence=0.9),
        altitude=ExtractedField(value="1350m", confidence=0.8),
    )

    # Exact source
    exact_source = RecipeSourceModel(
        id="src-exact",
        url="https://bluetokaicoffee.com/attikan-v60",
        title="Blue Tokai Attikan Estate V60 Recipe",
        author="Blue Tokai",
        raw_content="Pour-over brewing recipe for Attikan Estate washed coffee using Hario V60",
        content_hash="hash-1",
        coffee_metadata={
            "brand": "Blue Tokai Coffee Roasters",
            "estate": "Attikan Estate",
            "country": "India",
            "process": "Washed",
            "roast_level": "Medium-Dark"
        },
        extracted_recipe={
            "dripper": "Hario V60",
            "dose_g": 16.0,
            "water_g": 240.0,
            "ratio": "1:15",
            "water_temperature_c": 90,
            "grind_description": "Medium-coarse"
        }
    )

    # Related source (different coffee from India washed)
    related_source = RecipeSourceModel(
        id="src-related",
        url="https://kcroasters.com/kelagur-v60",
        title="KC Roasters Kelagur V60",
        author="KC Roasters",
        raw_content="Pour-over brewing recipe for Kelagur washed coffee",
        content_hash="hash-2",
        coffee_metadata={
            "brand": "KC Roasters",
            "estate": "Kelagur Estate",
            "country": "India",
            "process": "Washed",
            "roast_level": "Medium"
        },
        extracted_recipe={
            "dripper": "Hario V60",
            "dose_g": 15.0,
            "water_g": 240.0,
            "ratio": "1:16",
            "water_temperature_c": 92,
            "grind_description": "Medium"
        }
    )

    match_exact = MatchClassifier.score_and_classify(exact_source, draft, target_dripper="Hario V60")
    assert match_exact is not None
    assert match_exact.match_type in (MatchClassification.EXACT, MatchClassification.STRONG)
    assert match_exact.relevance_score >= 0.85

    match_related = MatchClassifier.score_and_classify(related_source, draft, target_dripper="Hario V60")
    assert match_related is not None
    assert match_related.match_type in (MatchClassification.RELATED, MatchClassification.ANALOGOUS)
    assert match_related.relevance_score < match_exact.relevance_score


def test_evidence_evaluator_outcomes_and_conflicts():
    from brewwise.services.retrieval.relevance import ScoredMatch

    # 1. Test Outcome A
    exact_match = ScoredMatch(
        source_id="src-1",
        url="https://source1.com/recipe",
        title="Exact Recipe",
        match_type=MatchClassification.EXACT,
        relevance_score=0.95,
        extracted_recipe={"dripper": "V60", "dose_g": 15.0, "water_g": 240.0, "water_temperature_c": 92, "ratio": "1:16"},
    )
    conflicting_match = ScoredMatch(
        source_id="src-2",
        url="https://source2.com/recipe",
        title="Conflicting Recipe",
        match_type=MatchClassification.STRONG,
        relevance_score=0.88,
        extracted_recipe={"dripper": "V60", "dose_g": 15.0, "water_g": 270.0, "water_temperature_c": 98, "ratio": "1:18"},
    )

    pkg_a = EvidenceEvaluator.evaluate([exact_match, conflicting_match])
    assert pkg_a.match_outcome == "A"
    assert len(pkg_a.matched_recipes) == 2
    # Verify conflict detection: temp difference is 98 - 92 = 6°C (> 5°C threshold) and ratio is 1:18 vs 1:16 (>= 1.2 threshold)
    assert len(pkg_a.conflicts) >= 1
    assert any(c.parameter == "Water Temperature" for c in pkg_a.conflicts)

    # 2. Test Outcome C (empty)
    pkg_c = EvidenceEvaluator.evaluate([])
    assert pkg_c.match_outcome == "C"
    assert pkg_c.matched_recipes == []


def test_provenance_verifier():
    from brewwise.services.retrieval.relevance import ScoredMatch
    from brewwise.services.retrieval.evidence_evaluator import EvidencePackage

    valid_url = "https://bluetokaicoffee.com/attikan-v60"
    match = ScoredMatch(
        source_id="src-1",
        url=valid_url,
        title="Attikan V60",
        author="Blue Tokai",
        match_type=MatchClassification.EXACT,
        relevance_score=0.96,
        extracted_recipe={"dripper": "Kalita Wave", "dose_g": 16.0, "water_g": 240.0, "water_temperature_c": 90},
    )

    evidence = EvidencePackage(
        match_outcome="A",
        matched_recipes=[match],
        conflicts=[],
        coverage_summary="Exact match",
        compact_context="Attikan V60"
    )

    recipe = PersonalisedRecipe(
        coffee_profile_id="p-1",
        dripper="Hario V60",
        dose_g=15.0,
        water_g=240.0,
        ratio="1:16",
        water_temperature_c=91,
        grind_description="Medium",
        bloom_water_g=45.0,
        bloom_time_seconds=45,
        target_brew_time_seconds=180,
        pour_schedule=[
            PourStep(step_number=1, water_g=45.0, cumulative_water_g=45.0, start_time_seconds=0, duration_seconds=15, technique="Bloom"),
            PourStep(step_number=2, water_g=195.0, cumulative_water_g=240.0, start_time_seconds=45, duration_seconds=30, technique="Main pour"),
        ],
        step_by_step_instructions=["Step 1", "Step 2"],
        expected_flavour="Dark chocolate",
        explanation=RecipeExplanation(reasoning_summary="Tested", parameter_rationale={}, assumptions=[]),
        troubleshooting=[],
        limitations=[],
        source_recipes=[
            SourceReference(source_name="Fabricated Source", url="https://fake-hallucinated-url.com/fake")
        ]
    )

    verified = ProvenanceVerifier.verify_and_ground(recipe, evidence)
    assert verified.source_type == "exact_match"
    # Hallucinated URL must NOT be in source_recipes
    assert not any("fake-hallucinated-url" in (s.url or "") for s in verified.source_recipes)
    # Valid verified URL should be attached
    assert any(s.url == valid_url for s in verified.source_recipes)
    # Equipment adaptation from Kalita Wave to Hario V60 should be noted
    assert any(a.parameter == "Dripper Geometry" for a in verified.adaptations)


def test_deduplicator_and_parser():
    text = (
        "Brewing guide for Subko Kerehaklu Estate Honey coffee.\n"
        "Recommended Pour-Over Recipe using Hario V60:\n"
        "- Dose: 15g freshly ground coffee\n"
        "- Water: 250g soft filtered water at 94°C (Ratio: 1:16.6)\n"
        "- Bloom: 45g water for 45s\n"
    )
    h1 = Deduplicator.compute_content_hash(text)
    h2 = Deduplicator.compute_content_hash(text.upper())
    assert h1 == h2

    parser = RecipeParser()
    recipe = parser._rule_based_parse(text, "https://subko.coffee/kerehaklu")
    assert recipe.dose_g == 15.0
    assert recipe.water_g == 250.0
    assert recipe.water_temperature_c == 94
    assert recipe.dripper == "Hario V60"
    assert recipe.process == "Honey"
