import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List
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
from brewwise.services.equipment.dripper_guide import get_dripper_details

from brewwise.services.retrieval.evidence_evaluator import EvidencePackage
from brewwise.services.synthesis.provenance_verifier import ProvenanceVerifier

logger = logging.getLogger(__name__)


STRENGTH_RATIO_SHIFT = {"light": 1.0, "balanced": 0.0, "strong": -1.0}

STANDARD_TROUBLESHOOTING = [
    TroubleshootingTip(
        symptom="Coffee tastes sour or hollow",
        likely_cause="Often under-extraction (water passing through too quickly), though very light roasts can simply be acidic",
        adjustment="Grind slightly finer first; if still sour next time, raise the water temperature by 1-2°C"
    ),
    TroubleshootingTip(
        symptom="Coffee tastes harsh, dry, or bitter",
        likely_cause="Often over-extraction or channelling from uneven pouring",
        adjustment="Grind slightly coarser first; if still bitter next time, lower the water temperature by 1-2°C"
    ),
    TroubleshootingTip(
        symptom="Coffee tastes weak or watery",
        likely_cause="Brew strength too low for your taste, or the grind is too coarse",
        adjustment="Use a tighter ratio (about 1g less water per gram of coffee) or grind slightly finer - change one at a time"
    ),
    TroubleshootingTip(
        symptom="Drawdown is slow or stalls",
        likely_cause="Grind too fine, fines clogging the filter, or too much agitation while pouring",
        adjustment="Grind slightly coarser and pour more gently; check the filter is seated properly and not clogged"
    ),
]


def ensure_troubleshooting_coverage(tips: List[TroubleshootingTip]) -> List[TroubleshootingTip]:
    """Guarantees tips for sourness, bitterness, weak flavour and slow drawdown."""
    covered = " ".join(t.symptom.lower() for t in tips)
    groups = [("sour",), ("bitter", "harsh", "astringent"), ("weak", "watery", "thin"), ("slow", "stall", "clog")]
    result = list(tips)
    for keywords, default_tip in zip(groups, STANDARD_TROUBLESHOOTING):
        if not any(k in covered for k in keywords):
            result.append(default_tip)
    return result


def _mmss(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def _g(value: float) -> str:
    return f"{value:g}"


def generate_baseline_recipe(
    coffee: CoffeeProfileDraft,
    dripper: str = "Hario V60",
    grinder: Optional[str] = None,
    dose_g: float = 15.0,
    target_strength: Optional[str] = "balanced",
    anchor: Optional[Dict[str, Any]] = None,
    anchor_title: Optional[str] = None
) -> RecipeGenerationOutput:
    """Deterministic rule-based starting recipe, used when no LLM is available or its output fails validation.
    Unknown coffee characteristics are stated as assumptions, never presented as facts."""
    roast_known = bool(coffee.roast_level.value)
    process_known = bool(coffee.process.value)
    roast = (coffee.roast_level.value or "").lower().replace("_", " ")
    process = (coffee.process.value or "").lower().replace("_", " ")

    assumptions = ["Soft filtered water", "Coffee rested at least a few days after roasting"]
    if "dark" in roast:
        temp, ratio_num, grind = 89, 15.0, "Medium-coarse (resembling sea salt)"
    elif "light" in roast and "medium" not in roast:
        temp, ratio_num, grind = 94, 16.0, "Medium-fine (resembling table salt)"
    else:
        temp, ratio_num, grind = 92, 16.0, "Medium (resembling sand)"
    if not roast_known:
        assumptions.append("Roast level is not stated on the bag; a middle-of-the-road 92°C starting point is used")
    if not process_known:
        assumptions.append("Processing method is not stated on the bag, so it did not inform this recipe")

    # Heavily fermented / natural lots tend to extract easily: start slightly cooler
    if any(k in process for k in ("natural", "anaerobic", "carbonic", "thermal")):
        temp -= 1

    # Anchor on a retrieved source recipe when one is available: its stated ratio,
    # temperature and grind replace the generic starting values.
    anchored: Dict[str, str] = {}
    if anchor:
        try:
            a_dose, a_water = float(anchor.get("dose_g") or 0), float(anchor.get("water_g") or 0)
            if a_dose > 0 and 12 <= a_water / a_dose <= 19:
                ratio_num = round(a_water / a_dose, 1)
                anchored["ratio"] = f"1:{_g(ratio_num)}"
        except (TypeError, ValueError):
            pass
        a_temp = anchor.get("water_temperature_c")
        if isinstance(a_temp, (int, float)) and 85 <= a_temp <= 99:
            temp = int(a_temp)
            anchored["temperature"] = f"{temp}°C"
        if anchor.get("grind_description"):
            grind = str(anchor["grind_description"])
            anchored["grind"] = grind

    ratio_num += STRENGTH_RATIO_SHIFT.get(target_strength or "balanced", 0.0)
    ratio = f"1:{_g(ratio_num)}"
    water_g = round(dose_g * ratio_num, 1)

    details = get_dripper_details(dripper) if dripper else None
    flat_bottom = bool(details and "flat" in details["geometry"].lower())

    bloom_water = round(dose_g * 3.0, 1)
    remaining_water = round(water_g - bloom_water, 1)
    # Flat-bottom brewers favour more, smaller pulses; cones work well with two larger pours
    pour_count = 3 if flat_bottom else 2
    bloom_time = 45
    interval = 35 if flat_bottom else 45
    # Larger brews need longer pours and a longer drawdown
    pour_duration = max(15, min(40, round(remaining_water / pour_count / 5)))
    target_time = bloom_time + interval * pour_count + max(45, round(dose_g * 3))

    main_technique = (
        "Gentle centre pulse pour keeping the water level even across the flat bed"
        if flat_bottom else
        "Steady spiral pour from the centre outward, avoiding the filter walls"
    )

    steps = [
        PourStep(
            step_number=1,
            water_g=bloom_water,
            cumulative_water_g=bloom_water,
            start_time_seconds=0,
            duration_seconds=15,
            technique="Gentle spiral pour saturating all dry grounds",
            notes=f"Let the coffee bloom until {_mmss(bloom_time)}"
        )
    ]
    cumulative = bloom_water
    for i in range(pour_count):
        is_last = i == pour_count - 1
        amount = round(water_g - cumulative, 1) if is_last else round(remaining_water / pour_count, 1)
        cumulative = water_g if is_last else round(cumulative + amount, 1)
        steps.append(
            PourStep(
                step_number=i + 2,
                water_g=amount,
                cumulative_water_g=cumulative,
                start_time_seconds=bloom_time + interval * i,
                duration_seconds=pour_duration,
                technique=main_technique,
                notes=(
                    f"Aim for full drawdown around {_mmss(target_time)}" if is_last
                    else f"Pour until the scale reads {_g(cumulative)}g"
                )
            )
        )

    instructions = [
        f"Place the filter in the {dripper}, rinse it with hot water, and discard the rinse water.",
        f"Add {_g(dose_g)}g of ground coffee, level the bed, and tare the scale.",
        f"Start the timer and pour {_g(bloom_water)}g of water at {temp}°C in gentle spirals. Wait until {_mmss(bloom_time)}.",
    ]
    for step in steps[1:]:
        instructions.append(
            f"At {_mmss(step.start_time_seconds)}, pour {_g(step.water_g)}g until the scale reads {_g(step.cumulative_water_g)}g."
        )
    instructions.append(f"Let the brew draw down completely (target about {_mmss(target_time)}), swirl, and serve.")

    notes = coffee.tasting_notes.value
    expected = (
        f"Prediction, not a guarantee: the bag lists {notes}; this recipe aims for a clean, balanced cup that lets those notes show."
        if notes else
        "Prediction, not a guarantee: a clean, balanced cup. No tasting notes were read from the bag."
    )

    roast_phrase = f"{roast} roast" if roast_known else "unstated roast level"
    rationale = {
        "temperature": (
            f"{temp}°C is a common starting point for a {roast_phrase}"
            + (f" with {process} processing" if process_known else "")
            + "; adjust by taste rather than treating it as the single correct value."
        ),
        "ratio": f"{ratio} targets {target_strength or 'balanced'} strength.",
        "bloom": f"{_g(bloom_water)}g (3x dose) lets trapped CO2 escape before the main pours.",
    }
    if details:
        rationale["dripper"] = f"{details['name']} ({details['geometry']}, flow: {details['flow_rate']}) shapes the pour structure."

    if anchored:
        source_label = anchor_title or "the top retrieved source"
        for key, value in anchored.items():
            rationale[key] = f"{value} is taken from {source_label}." + (
                f" Ratio then shifted for {target_strength} strength." if key == "ratio" and target_strength in ("light", "strong") else ""
            )
        limitations = [f"Ratio, temperature and grind follow {source_label}; the pour schedule is a standard structure scaled to your dose"]
    else:
        limitations = ["Rule-based starting recipe: not derived from a published recipe for this coffee"]
    if dripper and not details:
        limitations.append(f"'{dripper}' is not in the equipment catalogue, so a generic pour structure is used")

    return RecipeGenerationOutput(
        dose_g=dose_g,
        water_g=water_g,
        ratio=ratio,
        water_temperature_c=temp,
        grind_description=grind,
        grind_setting=None,
        filter_prep="Rinse paper filter with hot water and discard rinse water.",
        bloom_water_g=bloom_water,
        bloom_time_seconds=bloom_time,
        pour_schedule=steps,
        target_brew_time_seconds=target_time,
        step_by_step_instructions=instructions,
        expected_flavour=expected,
        explanation=RecipeExplanation(
            reasoning_summary=(
                f"Starting recipe built from general pour-over principles for a {roast_phrase}"
                + (f", {process} coffee" if process_known else " coffee")
                + f": {ratio} at {temp}°C."
            ) if not anchored else (
                f"Parameters ({', '.join(anchored)}) follow {anchor_title or 'the top retrieved source'}, "
                f"scaled to a {_g(dose_g)}g dose: {ratio} at {temp}°C."
            ),
            parameter_rationale=rationale,
            assumptions=assumptions
        ),
        troubleshooting=list(STANDARD_TROUBLESHOOTING),
        limitations=limitations
    )


class RecipeGenerator:
    MAX_SYNTHESIS_CALLS: int = 1
    generate_fallback_baseline = staticmethod(generate_baseline_recipe)

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
        grinder = (request.grinder or "").strip() or None

        # Cache key covers everything that shapes the recipe: the (possibly user-corrected)
        # profile values, the equipment/preferences, and the evidence actually retrieved.
        fingerprint = json.dumps({
            "profile": {
                name: getattr(coffee, name).value
                for name in ("brand", "product_name", "estate", "country", "region", "varietal",
                             "process", "roast_level", "tasting_notes", "altitude")
            },
            "request": [dripper, grinder, dose, request.target_strength],
            "evidence": [evidence.match_outcome, [m.url for m in evidence.matched_recipes[:3]]] if evidence else None,
        }, sort_keys=True, default=str)
        cache_key = f"recipe:v2:{coffee.id}:{hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()[:32]}"
        if self.cache_provider:
            cached = await self.cache_provider.get(cache_key)
            if cached:
                try:
                    return PersonalisedRecipe.model_validate_json(cached)
                except Exception:
                    pass

        generation_output: Optional[RecipeGenerationOutput] = None
        used_llm = False

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
                        used_llm = True
                        break
                    else:
                        logger.warning(f"Recipe validation failed on attempt {attempt}: {errors}")
                        prompt += f"\nValidation failed with errors: {'; '.join(errors)}. Please correct these numbers."
                except Exception as e:
                    logger.warning(f"LLM generation attempt {attempt} failed: {e}")

        # Fallback to deterministic expert baseline if LLM fails or is unconfigured
        anchored_on_source = False
        if not generation_output:
            best = evidence.matched_recipes[0] if (evidence and evidence.match_outcome in ("A", "B") and evidence.matched_recipes) else None
            generation_output = generate_baseline_recipe(
                coffee=coffee,
                dripper=dripper,
                grinder=grinder,
                dose_g=dose,
                target_strength=request.target_strength,
                anchor=best.extracted_recipe if best else None,
                anchor_title=best.title if best else None
            )
            anchored_on_source = best is not None
            if self.llm_provider:
                generation_output.limitations.append(
                    "The AI model was unavailable or returned an inconsistent recipe, so a rule-based starting recipe is shown instead"
                )

        from brewwise.services.equipment.grinder_guide import map_grind_setting

        # Grinder-specific settings come only from the equipment catalogue. A setting the
        # model volunteers for a grinder we have no data on is not shown as fact.
        limitations = list(generation_output.limitations)
        resolved_grind_setting = map_grind_setting(grinder, generation_output.grind_description) if grinder else None
        if grinder and not resolved_grind_setting:
            limitations.append(
                f"No verified setting data for '{grinder}': use the relative grind description, "
                "then go finer if the cup is sour/fast or coarser if it is bitter/slow"
            )

        if evidence and evidence.match_outcome == "A":
            confidence = 0.9 if used_llm else 0.8
        elif evidence and evidence.match_outcome == "B":
            confidence = 0.75 if used_llm else 0.65
        else:
            confidence = 0.6 if used_llm else 0.5

        expected_flavour = generation_output.expected_flavour
        if "prediction" not in expected_flavour.lower():
            expected_flavour = f"Prediction, not a guarantee: {expected_flavour}"

        # Assemble full PersonalisedRecipe
        recipe = PersonalisedRecipe(
            coffee_profile_id=coffee.id,
            source_type="ai_generated" if (used_llm or anchored_on_source) else "curated_baseline",
            generation_model=self.model_name if used_llm else "baseline-rule-engine",
            dripper=dripper,
            grinder=grinder,
            filter_type="Paper",
            dose_g=generation_output.dose_g,
            water_g=generation_output.water_g,
            ratio=generation_output.ratio,
            water_temperature_c=generation_output.water_temperature_c,
            grind_description=generation_output.grind_description,
            grind_setting=resolved_grind_setting,
            filter_prep=generation_output.filter_prep,
            bloom_water_g=generation_output.bloom_water_g,
            bloom_time_seconds=generation_output.bloom_time_seconds,
            pour_schedule=generation_output.pour_schedule,
            target_brew_time_seconds=generation_output.target_brew_time_seconds,
            step_by_step_instructions=generation_output.step_by_step_instructions,
            expected_flavour=expected_flavour,
            explanation=generation_output.explanation,
            troubleshooting=ensure_troubleshooting_coverage(generation_output.troubleshooting),
            limitations=limitations,
            confidence=confidence
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
