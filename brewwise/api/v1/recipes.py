import logging
from typing import Optional
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
    PourStep,
    RecipeExplanation,
    TroubleshootingTip,
)
from brewwise.dependencies import get_recipe_generator
from brewwise.services.synthesis.recipe_generator import RecipeGenerator

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Recipes & Profiles"])


@router.get("/profiles/{profile_id}", response_model=CoffeeProfileDraft)
async def get_coffee_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CoffeeProfileModel).where(CoffeeProfileModel.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Coffee profile not found")

    if profile.raw_metadata:
        return CoffeeProfileDraft.model_validate(profile.raw_metadata)

    # Construct draft if raw_metadata wasn't stored
    return CoffeeProfileDraft(
        id=profile.id,
        brand=ExtractedField(value=profile.brand, confidence=profile.confidence),
        product_name=ExtractedField(value=profile.product_name, confidence=profile.confidence),
        estate=ExtractedField(value=profile.estate, confidence=profile.confidence),
        country=ExtractedField(value=profile.country, confidence=profile.confidence),
        region=ExtractedField(value=profile.region, confidence=profile.confidence),
        varietal=ExtractedField(value=profile.varietal, confidence=profile.confidence),
        process=ExtractedField(value=profile.process, confidence=profile.confidence),
        roast_level=ExtractedField(value=profile.roast_level, confidence=profile.confidence),
        roast_date=ExtractedField(value=profile.roast_date, confidence=profile.confidence),
        tasting_notes=ExtractedField(value=profile.tasting_notes, confidence=profile.confidence),
        altitude=ExtractedField(value=profile.altitude, confidence=profile.confidence),
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
    draft_dict = profile.raw_metadata or {}
    for field, val in update_data.items():
        if field in draft_dict:
            draft_dict[field]["value"] = val
            draft_dict[field]["source"] = "user_override"
            draft_dict[field]["confidence"] = 1.0

    profile.raw_metadata = draft_dict
    await db.commit()

    return await get_coffee_profile(profile_id, db)


@router.post("/recipes/generate", response_model=PersonalisedRecipe)
async def generate_recipe(
    request: RecipeGenerateRequest,
    generator: RecipeGenerator = Depends(get_recipe_generator),
    db: AsyncSession = Depends(get_db)
):
    # Fetch profile
    profile_draft = await get_coffee_profile(request.coffee_profile_id, db)

    # Generate recipe
    recipe = await generator.generate(profile_draft, request)

    # Save to db
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
        limitations=item.limitations or [],
        confidence=item.confidence,
        created_at=item.created_at
    )
