from typing import List, Optional
from brewwise.schemas.recipe import SourceReference, Adaptation, PersonalisedRecipe
from brewwise.services.retrieval.evidence_evaluator import EvidencePackage


class ProvenanceVerifier:
    @classmethod
    def verify_and_ground(
        cls,
        recipe: PersonalisedRecipe,
        evidence: Optional[EvidencePackage]
    ) -> PersonalisedRecipe:
        """Strictly verifies citations against retrieved sources in code.
        Replaces any fabricated or hallucinated URLs with verified references."""
        if not evidence or not evidence.matched_recipes or evidence.match_outcome == "C":
            # No retrieved evidence - must be AI generated from principles
            recipe.source_type = "ai_generated" if recipe.source_type != "curated_baseline" else "curated_baseline"
            recipe.source_recipes = []
            note = "No sufficiently relevant published recipe was found in the searched sources; this is a generated starting point"
            if note not in recipe.limitations:
                recipe.limitations.append(note)
            return recipe

        # Build set of valid URLs from evidence
        valid_urls = {m.url for m in evidence.matched_recipes if m.url}
        url_to_match = {m.url: m for m in evidence.matched_recipes if m.url}

        verified_sources: List[SourceReference] = []

        # If LLM generated source references, verify each one
        for ref in recipe.source_recipes:
            if ref.url and ref.url in valid_urls:
                verified_sources.append(ref)
            else:
                # LLM hallucinated a URL or gave an invalid reference
                pass

        # If no verified sources from LLM or LLM output empty, attach top verified sources from evidence
        if not verified_sources and evidence.matched_recipes:
            for m in evidence.matched_recipes[:2]:
                verified_sources.append(
                    SourceReference(
                        source_name=f"{m.author or m.site_name or 'Retrieved source'} ({m.title})",
                        url=m.url,
                        similarity_score=m.relevance_score
                    )
                )

        recipe.source_recipes = verified_sources

        # Set correct source_type based on verified outcome
        if recipe.source_type == "curated_baseline":
            # Rule-based fallback did not use the sources' parameters: list them as references only
            recipe.limitations.append(
                "Retrieved sources are listed for reference; this rule-based recipe was not derived from their parameters"
            )
            return recipe

        if evidence.match_outcome == "A":
            recipe.source_type = "exact_match"
        elif evidence.match_outcome == "B":
            recipe.source_type = "adapted_from_related"
        else:
            recipe.source_type = "ai_generated"

        # Generate adaptations if user equipment differed from source equipment
        if evidence.matched_recipes:
            best_match = evidence.matched_recipes[0]
            src_dripper = best_match.extracted_recipe.get("dripper")
            src_dose = best_match.extracted_recipe.get("dose_g")
            src_temp = best_match.extracted_recipe.get("water_temperature_c")

            if src_dripper and src_dripper.lower() != recipe.dripper.lower():
                recipe.adaptations.append(
                    Adaptation(
                        parameter="Dripper Geometry",
                        original_value=src_dripper,
                        adapted_value=recipe.dripper,
                        rationale=f"Adapted pour structure and flow rate for {recipe.dripper} from source {src_dripper} recipe."
                    )
                )

            if src_dose and abs(src_dose - recipe.dose_g) >= 1.0:
                recipe.adaptations.append(
                    Adaptation(
                        parameter="Brew Dose & Yield",
                        original_value=f"{src_dose}g coffee",
                        adapted_value=f"{recipe.dose_g}g coffee ({recipe.water_g}g water)",
                        rationale=f"Scaled water and pour schedule proportionally to match user requested {recipe.dose_g}g dose."
                    )
                )

        return recipe
