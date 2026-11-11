import json
import logging
from pathlib import Path
from typing import Optional, List
from jinja2 import Template

from brewwise.providers.llm.base import LLMProvider
from brewwise.providers.cache.base import CacheProvider
from brewwise.schemas.coffee_profile import CoffeeProfileDraft
from brewwise.schemas.recipe import (
    RecipeGenerationOutput,
    PersonalisedRecipe,
    PourStep,
    RecipeExplanation,
    TroubleshootingTip,
    RecipeGenerateRequest,
)
from brewwise.services.synthesis.validator import RecipeValidator

from brewwise.services.retrieval.evidence_evaluator import EvidencePackage
from brewwise.services.synthesis.provenance_verifier import ProvenanceVerifier

logger = logging.getLogger(__name__)


def generate_baseline_recipe(
    coffee: CoffeeProfileDraft,
    dripper: str = "Hario V60",
    grinder: Optional[str] = None,
    dose_g: float = 15.0
) -> RecipeGenerationOutput:
    """Deterministic fallback expert recipe when LLM is unavailable or for offline testing."""
    roast = (coffee.roast_level.value or "medium").lower()
    process = (coffee.process.value or "washed").lower()

    if "dark" in roast:
        temp = 89
        ratio = "1:15"
        water_g = dose_g * 15.0
        grind = "Medium-coarse (resembling sea salt)"
    elif "light" in roast:
        temp = 94
        ratio = "1:16"
        water_g = dose_g * 16.0
        grind = "Medium-fine (resembling table salt)"
    else:
        temp = 92
        ratio = "1:16"
        water_g = dose_g * 16.0
        grind = "Medium (resembling sand)"

    bloom_water = round(dose_g * 3.0, 1)
    remaining_water = water_g - bloom_water
    pour2 = round(remaining_water * 0.5, 1)
    pour3 = round(remaining_water - pour2, 1)

    steps = [
        PourStep(
            step_number=1,
            water_g=bloom_water,
            cumulative_water_g=bloom_water,
            start_time_seconds=0,
            duration_seconds=15,
            technique="Gentle spiral pour saturating all dry grounds",
            notes="Swirl gently or allow grounds to bloom until 0:45"
        ),
        PourStep(
            step_number=2,
            water_g=pour2,
            cumulative_water_g=round(bloom_water + pour2, 1),
            start_time_seconds=45,
            duration_seconds=25,
            technique="Continuous steady spiral pour from centre to edge without washing sides",
            notes="Maintain steady flow rate"
        ),
        PourStep(
            step_number=3,
            water_g=pour3,
            cumulative_water_g=water_g,
            start_time_seconds=90,
            duration_seconds=25,
            technique="Centre pulse pour to reach final brew weight",
            notes="Allow complete drawdown by 2:45 - 3:15"
        ),
    ]

    return RecipeGenerationOutput(
        dose_g=dose_g,
        water_g=water_g,
        ratio=ratio,
        water_temperature_c=temp,
        grind_description=grind,
        grind_setting=None,
        filter_prep="Rinse paper filter with hot water and discard rinse water.",
        bloom_water_g=bloom_water,
        bloom_time_seconds=45,
        pour_schedule=steps,
        target_brew_time_seconds=180,
        step_by_step_instructions=[
            f"Preheat {dripper} and thoroughly rinse paper filter.",
            f"Add {dose_g}g of ground coffee, tap gently to level bed, and tare scale.",
            f"Start timer and pour {bloom_water}g water at {temp}°C in gentle spirals. Wait until 0:45.",
            f"At 0:45, pour steadily until scale reads {bloom_water + pour2}g.",
            f"At 1:30, pour final water until total weight reaches {water_g}g.",
            "Let draw down completely, swirl carafe, and enjoy!"
        ],
        expected_flavour=f"Clean, expressive notes highlighted by {coffee.tasting_notes.value or 'sweet clarity'}.",
        explanation=RecipeExplanation(
            reasoning_summary=f"Tailored {ratio} ratio and {temp}°C water to extract optimal sweetness from {roast} roasted, {process} coffee.",
            parameter_rationale={
                "temperature": f"{temp}°C chosen to balance extraction without extracting harsh roasty bitter notes.",
                "ratio": f"{ratio} delivers balanced strength and high flavor clarity on a conical dripper.",
                "bloom": f"{bloom_water}g (3x dose) allows trapped CO2 to fully escape."
            },
            assumptions=["Soft filtered water with 50-90 ppm TDS", "Freshly roasted specialty beans"]
        ),
        troubleshooting=[
            TroubleshootingTip(
                symptom="Coffee tastes sour or hollow",
                likely_cause="Under-extraction or water flowing too quickly",
                adjustment="Grind slightly finer or increase water temperature by 2°C"
            ),
            TroubleshootingTip(
                symptom="Coffee tastes harsh, dry, or bitter",
                likely_cause="Over-extraction or channelling",
                adjustment="Grind slightly coarser or decrease water temperature by 2°C"
            )
        ],
        limitations=["Assumes standard paper filter and room temperature dripper preheating"]
    )


class RecipeGenerator:
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        cache_provider: Optional[CacheProvider] = None,
        model_name: str = "gemini-2.5-flash"
    ):
        self.llm_provider = llm_provider
        self.cache_provider = cache_provider
        self.model_name = model_name

        prompts_dir = Path(__file__).parent.parent.parent / "prompts" / "v1"
        prompt_path = prompts_dir / "generate_recipe.j2"
        grounded_prompt_path = prompts_dir / "generate_grounded_recipe.j2"

        if prompt_path.exists():
            self.template = Template(prompt_path.read_text(encoding="utf-8"))
        else:
            self.template = None

        if grounded_prompt_path.exists():
            self.grounded_template = Template(grounded_prompt_path.read_text(encoding="utf-8"))
        else:
            self.grounded_template = None

    async def generate(
        self,
        coffee: CoffeeProfileDraft,
        request: RecipeGenerateRequest,
        evidence: Optional[EvidencePackage] = None
    ) -> PersonalisedRecipe:
        dose = request.dose_preference_g or 15.0
        dripper = request.dripper or "Hario V60"
        grinder = request.grinder or "Specialty Grinder"

        # Check cache
        outcome_code = evidence.match_outcome if evidence else "none"
        cache_key = f"recipe:{coffee.id}:{dripper}:{dose}:{request.target_strength}:{outcome_code}"
        if self.cache_provider:
            cached = await self.cache_provider.get(cache_key)
            if cached:
                try:
                    return PersonalisedRecipe.model_validate_json(cached)
                except Exception:
                    pass

        generation_output: Optional[RecipeGenerationOutput] = None

        # Choose template: grounded if evidence exists, otherwise standard
        active_template = self.grounded_template if (evidence and self.grounded_template) else self.template

        if self.llm_provider and active_template:
            template_kwargs = {
                "coffee": coffee,
                "dripper": dripper,
                "grinder": grinder,
                "dose_g": dose,
                "target_strength": request.target_strength
            }
            if evidence:
                template_kwargs["evidence"] = evidence

            prompt = active_template.render(**template_kwargs)

            for attempt in range(2):
                try:
                    output = await self.llm_provider.generate_structured(
                        prompt=prompt,
                        response_schema=RecipeGenerationOutput,
                        system_instruction="You are a champion barista crafting precision pour-over recipes. Follow exact arithmetic and ground every decision.",
                        model=self.model_name
                    )
                    valid, errors = RecipeValidator.validate(output)
                    if valid:
                        generation_output = output
                        break
                    else:
                        logger.warning(f"Recipe validation failed on attempt {attempt}: {errors}")
                        prompt += f"\nValidation failed with errors: {'; '.join(errors)}. Please correct these numbers."
                except Exception as e:
                    logger.warning(f"LLM generation attempt {attempt} failed: {e}")

        # Fallback to deterministic expert baseline if LLM fails or is unconfigured
        if not generation_output:
            generation_output = generate_baseline_recipe(
                coffee=coffee,
                dripper=dripper,
                grinder=grinder,
                dose_g=dose
            )

        # Assemble full PersonalisedRecipe
        recipe = PersonalisedRecipe(
            coffee_profile_id=coffee.id,
            source_type="ai_generated" if self.llm_provider else "curated_baseline",
            generation_model=self.model_name if self.llm_provider else "baseline-rule-engine",
            dripper=dripper,
            grinder=grinder,
            filter_type="Paper",
            dose_g=generation_output.dose_g,
            water_g=generation_output.water_g,
            ratio=generation_output.ratio,
            water_temperature_c=generation_output.water_temperature_c,
            grind_description=generation_output.grind_description,
            grind_setting=generation_output.grind_setting,
            filter_prep=generation_output.filter_prep,
            bloom_water_g=generation_output.bloom_water_g,
            bloom_time_seconds=generation_output.bloom_time_seconds,
            pour_schedule=generation_output.pour_schedule,
            target_brew_time_seconds=generation_output.target_brew_time_seconds,
            step_by_step_instructions=generation_output.step_by_step_instructions,
            expected_flavour=generation_output.expected_flavour,
            explanation=generation_output.explanation,
            troubleshooting=generation_output.troubleshooting,
            limitations=generation_output.limitations,
            confidence=0.92 if (evidence and evidence.match_outcome == "A") else 0.88
        )

        # Verify and apply grounded provenance
        recipe = ProvenanceVerifier.verify_and_ground(recipe, evidence)

        # Cache valid recipe (24 hours)
        if self.cache_provider:
            try:
                await self.cache_provider.set(cache_key, recipe.model_dump_json(), ttl_seconds=86400)
            except Exception:
                pass

        return recipe
