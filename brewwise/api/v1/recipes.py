import hashlib
import json
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from brewwise.db.session import get_db
from brewwise.models.coffee_profile import CoffeeProfileModel
from brewwise.models.recipe import RecipeModel
from brewwise.schemas.coffee_profile import CoffeeProfileDraft, ExtractedField, CoffeeProfileUpdate
from brewwise.schemas.recipe import (
    PersonalisedRecipe,
    RecipeGenerateRequest,
    RecipeSearchRequest,
    PourStep,
    RecipeExplanation,
    TroubleshootingTip,
    SourceReference,
    Adaptation,
)
from brewwise.config import settings
from brewwise.providers.cache.base import CacheProvider
from brewwise.dependencies import (
    get_cache_provider,
    get_recipe_generator,
    get_hybrid_retriever,
    get_discovery_orchestrator,
)
from brewwise.services.synthesis.recipe_generator import RecipeGenerator
from brewwise.services.retrieval.hybrid_retriever import HybridRetriever
from brewwise.services.retrieval.query_builder import QueryBuilder
from brewwise.services.retrieval.relevance import MatchClassifier
from brewwise.services.retrieval.evidence_evaluator import EvidenceEvaluator, EvidencePackage
from brewwise.services.discovery.orchestrator import DiscoveryOrchestrator
from brewwise.services.discovery.result_merger import ResultMerger

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Recipes & Profiles"])


@router.get("/profiles/{profile_id}", response_model=CoffeeProfileDraft)
async def get_coffee_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CoffeeProfileModel).where(CoffeeProfileModel.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Coffee profile not found")

    if profile.raw_metadata:
        try:
            return CoffeeProfileDraft.model_validate(profile.raw_metadata)
        except Exception as e:
            logger.warning(f"Could not validate raw_metadata directly for {profile_id}: {e}")

    # Construct draft if raw_metadata wasn't stored or failed validation
    return CoffeeProfileDraft(
        id=profile.id,
        brand=ExtractedField(value=profile.brand, confidence=profile.confidence, source="user_override" if profile.brand else "unknown"),
        product_name=ExtractedField(value=profile.product_name, confidence=profile.confidence, source="user_override" if profile.product_name else "unknown"),
        estate=ExtractedField(value=profile.estate, confidence=profile.confidence, source="user_override" if profile.estate else "unknown"),
        country=ExtractedField(value=profile.country, confidence=profile.confidence, source="user_override" if profile.country else "unknown"),
        region=ExtractedField(value=profile.region, confidence=profile.confidence, source="user_override" if profile.region else "unknown"),
        varietal=ExtractedField(value=profile.varietal, confidence=profile.confidence, source="user_override" if profile.varietal else "unknown"),
        process=ExtractedField(value=profile.process, confidence=profile.confidence, source="user_override" if profile.process else "unknown"),
        roast_level=ExtractedField(value=profile.roast_level, confidence=profile.confidence, source="user_override" if profile.roast_level else "unknown"),
        roast_date=ExtractedField(value=profile.roast_date, confidence=profile.confidence, source="user_override" if profile.roast_date else "unknown"),
        tasting_notes=ExtractedField(value=profile.tasting_notes, confidence=profile.confidence, source="user_override" if profile.tasting_notes else "unknown"),
        altitude=ExtractedField(value=profile.altitude, confidence=profile.confidence, source="user_override" if profile.altitude else "unknown"),
        image_url=profile.image_url,
    )


@router.put("/profiles/{profile_id}", response_model=CoffeeProfileDraft)
async def update_coffee_profile(
    profile_id: str,
    update: CoffeeProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(CoffeeProfileModel).where(CoffeeProfileModel.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Coffee profile not found")

    update_data = update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if hasattr(profile, field):
            setattr(profile, field, val)

    # Update raw_metadata if present
    draft_dict = dict(profile.raw_metadata) if profile.raw_metadata else {}
    for field, val in update_data.items():
        if field in draft_dict and isinstance(draft_dict[field], dict):
            draft_dict[field]["value"] = val
            draft_dict[field]["source"] = "user_override"
            draft_dict[field]["confidence"] = 1.0
        elif val is not None:
            draft_dict[field] = {"value": val, "source": "user_override", "confidence": 1.0}

    profile.raw_metadata = draft_dict
    await db.commit()

    return await get_coffee_profile(profile_id, db)


def _evidence_cache_key(profile: CoffeeProfileDraft, dripper: Optional[str]) -> str:
    fingerprint = json.dumps(
        {
            "fields": {
                name: getattr(profile, name).value
                for name in ("brand", "product_name", "estate", "country", "region", "varietal", "process", "roast_level")
            },
            "dripper": dripper,
        },
        sort_keys=True,
        default=str,
    )
    return f"evidence:v1:{hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()}"


def _classify(candidates, profile: CoffeeProfileDraft, dripper: Optional[str]):
    matches = []
    for source, score in candidates:
        match = MatchClassifier.score_and_classify(
            source=source,
            profile=profile,
            target_dripper=dripper,
            base_retrieval_score=score
        )
        if match:
            matches.append(match)
    return matches


async def gather_evidence(
    profile: CoffeeProfileDraft,
    dripper: Optional[str],
    retriever: HybridRetriever,
    discovery: DiscoveryOrchestrator,
    db: AsyncSession,
    cache: Optional[CacheProvider] = None,
) -> EvidencePackage:
    """Knowledge-base retrieval + live web discovery + relevance evaluation.

    Shared by /recipes/search and /recipes/generate. The result is cached briefly so the
    generate call that follows a search does not repeat retrieval, web search and extraction.
    """
    cache_key = _evidence_cache_key(profile, dripper)
    if cache:
        try:
            cached = await cache.get(cache_key)
            if cached:
                return EvidencePackage.model_validate_json(cached)
        except Exception as e:
            logger.debug(f"Evidence cache read failed: {e}")

    # 1. Local hybrid retrieval
    queries = QueryBuilder.build_queries(profile, dripper=dripper)
    local_candidates = await retriever.search(queries, db, top_k=20)
    local_matches = _classify(local_candidates, profile, dripper)
    top_score = max((m.relevance_score for m in local_matches), default=0.0)

    # 2. Live web discovery (skipped only when the KB already has an exact match)
    discovery_res = await discovery.discover(
        profile=profile,
        db=db,
        kb_matches_count=len(local_matches),
        kb_top_score=top_score
    )

    # 3. Merge, rerank and evaluate
    merged_candidates = ResultMerger.merge(discovery_res.discovered_recipes, local_candidates)
    evidence = EvidenceEvaluator.evaluate(
        matches=_classify(merged_candidates, profile, dripper),
        discovery_status=discovery_res.search_status,
        discovery_message=discovery_res.message,
        urls_searched=discovery_res.urls_attempted,
        recipes_discovered=discovery_res.urls_yielded_recipes
    )

    # Failed or partial searches are not cached, so the next request retries them
    if cache and discovery_res.search_status not in ("failed", "partial"):
        try:
            await cache.set(cache_key, evidence.model_dump_json(), ttl_seconds=settings.EVIDENCE_CACHE_TTL_SECONDS)
        except Exception as e:
            logger.debug(f"Evidence cache write failed: {e}")

    return evidence


@router.post("/recipes/search", response_model=EvidencePackage)
async def search_recipes(
    request: RecipeSearchRequest,
    retriever: HybridRetriever = Depends(get_hybrid_retriever),
    discovery: DiscoveryOrchestrator = Depends(get_discovery_orchestrator),
    cache: CacheProvider = Depends(get_cache_provider),
    db: AsyncSession = Depends(get_db)
):
    """Local hybrid retrieval + inline live web discovery, with match classification."""
    profile_draft = await get_coffee_profile(request.coffee_profile_id, db)
    return await gather_evidence(profile_draft, request.dripper, retriever, discovery, db, cache)


@router.post("/recipes/generate", response_model=PersonalisedRecipe)
async def generate_recipe(
    request: RecipeGenerateRequest,
    generator: RecipeGenerator = Depends(get_recipe_generator),
    retriever: HybridRetriever = Depends(get_hybrid_retriever),
    discovery: DiscoveryOrchestrator = Depends(get_discovery_orchestrator),
    cache: CacheProvider = Depends(get_cache_provider),
    db: AsyncSession = Depends(get_db)
):
    profile_draft = await get_coffee_profile(request.coffee_profile_id, db)
    evidence_pkg = await gather_evidence(profile_draft, request.dripper, retriever, discovery, db, cache)

    # Grounded recipe generation (single call)
    recipe = await generator.generate(profile_draft, request, evidence=evidence_pkg)

    # Save to db if not already inserted
    existing_recipe = await db.get(RecipeModel, recipe.recipe_id)
    if not existing_recipe:
        db_recipe = RecipeModel(
            id=recipe.recipe_id,
            coffee_profile_id=recipe.coffee_profile_id,
            source_type=recipe.source_type,
            generation_model=recipe.generation_model,
            dripper=recipe.dripper,
            grinder=recipe.grinder,
            filter_type=recipe.filter_type,
            dose_g=recipe.dose_g,
            water_g=recipe.water_g,
            ratio=recipe.ratio,
            water_temperature_c=recipe.water_temperature_c,
            grind_description=recipe.grind_description,
            grind_setting=recipe.grind_setting,
            filter_prep=recipe.filter_prep,
            bloom_water_g=recipe.bloom_water_g,
            bloom_time_seconds=recipe.bloom_time_seconds,
            target_brew_time_seconds=recipe.target_brew_time_seconds,
            pour_schedule=[p.model_dump(mode="json") for p in recipe.pour_schedule],
            step_by_step_instructions=recipe.step_by_step_instructions,
            expected_flavour=recipe.expected_flavour,
            explanation=recipe.explanation.model_dump(mode="json"),
            troubleshooting=[t.model_dump(mode="json") for t in recipe.troubleshooting],
            limitations=recipe.limitations,
            source_recipes=[s.model_dump(mode="json") for s in recipe.source_recipes],
            adaptations=[a.model_dump(mode="json") for a in recipe.adaptations],
            confidence=recipe.confidence
        )
        db.add(db_recipe)
        await db.commit()

    return recipe


@router.get("/recipes/{recipe_id}", response_model=PersonalisedRecipe)
async def get_recipe(recipe_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RecipeModel).where(RecipeModel.id == recipe_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Recipe not found")

    pour_steps = [PourStep(**p) for p in item.pour_schedule]
    explanation = RecipeExplanation(**(item.explanation or {"reasoning_summary": ""}))
    troubleshooting = [TroubleshootingTip(**t) for t in (item.troubleshooting or [])]
    source_recipes = [SourceReference(**s) for s in (item.source_recipes or [])]
    adaptations = [Adaptation(**a) for a in (item.adaptations or [])]

    return PersonalisedRecipe(
        recipe_id=item.id,
        coffee_profile_id=item.coffee_profile_id,
        source_type=item.source_type,
        generation_model=item.generation_model,
        dripper=item.dripper,
        grinder=item.grinder,
        filter_type=item.filter_type,
        dose_g=item.dose_g,
        water_g=item.water_g,
        ratio=item.ratio,
        water_temperature_c=item.water_temperature_c,
        grind_description=item.grind_description,
        grind_setting=item.grind_setting,
        filter_prep=item.filter_prep,
        bloom_water_g=item.bloom_water_g,
        bloom_time_seconds=item.bloom_time_seconds,
        pour_schedule=pour_steps,
        target_brew_time_seconds=item.target_brew_time_seconds,
        step_by_step_instructions=item.step_by_step_instructions,
        expected_flavour=item.expected_flavour or "",
        explanation=explanation,
        troubleshooting=troubleshooting,
        source_recipes=source_recipes,
        adaptations=adaptations,
        limitations=item.limitations or [],
        confidence=item.confidence,
        created_at=item.created_at
    )
