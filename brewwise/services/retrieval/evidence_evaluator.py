from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from brewwise.services.retrieval.relevance import ScoredMatch, MatchClassification


class ParameterConflict(BaseModel):
    parameter: str
    difference: str
    sources_involved: List[str]
    resolution_guidance: str


class EvidencePackage(BaseModel):
    match_outcome: Literal["A", "B", "C"]
    matched_recipes: List[ScoredMatch] = Field(default_factory=list)
    conflicts: List[ParameterConflict] = Field(default_factory=list)
    coverage_summary: str
    compact_context: str
    discovery_status: Optional[str] = "disabled"
    discovery_message: Optional[str] = None
    urls_searched: int = 0
    recipes_discovered: int = 0


class EvidenceEvaluator:
    @classmethod
    def evaluate(
        cls,
        matches: List[ScoredMatch],
        discovery_status: Optional[str] = "disabled",
        discovery_message: Optional[str] = None,
        urls_searched: int = 0,
        recipes_discovered: int = 0
    ) -> EvidencePackage:
        """Deterministically evaluates retrieved candidates and forms an EvidencePackage."""
        if not matches:
            return EvidencePackage(
                match_outcome="C",
                matched_recipes=[],
                conflicts=[],
                coverage_summary=(
                    "No sufficiently relevant pour-over recipe was found in the searchable sources for this coffee. "
                    "The recipe is an AI-generated starting point based on general brewing principles."
                ),
                compact_context="NO_RETRIEVED_RECIPES",
                discovery_status=discovery_status,
                discovery_message=discovery_message,
                urls_searched=urls_searched,
                recipes_discovered=recipes_discovered
            )

        # Sort matches by relevance score descending
        sorted_matches = sorted(matches, key=lambda m: m.relevance_score, reverse=True)

        has_exact_or_strong = any(
            m.match_type in (MatchClassification.EXACT, MatchClassification.STRONG)
            for m in sorted_matches
        )
        has_related_or_analogous = any(
            m.match_type in (MatchClassification.RELATED, MatchClassification.ANALOGOUS)
            for m in sorted_matches
        )

        if has_exact_or_strong:
            outcome: Literal["A", "B", "C"] = "A"
            best = next(m for m in sorted_matches if m.match_type in (MatchClassification.EXACT, MatchClassification.STRONG))
            coverage = f"Found a recipe for this coffee from {best.author or best.site_name or 'a retrieved source'} ({best.title})."
        elif has_related_or_analogous:
            outcome = "B"
            best = sorted_matches[0]
            coverage = (
                "No recipe was found for this exact coffee. Recipes for related coffees "
                f"(e.g. {best.title}) are used as references, not as verified recipes for this coffee."
            )
        else:
            outcome = "C"
            coverage = "Only general references found. Synthesizing from foundational pour-over science."

        # Detect conflicts among top 3 matches
        conflicts = cls._detect_conflicts(sorted_matches[:3])

        # Build compact context for synthesis prompt (token-efficient)
        compact_lines = []
        for i, m in enumerate(sorted_matches[:3], 1):
            r = m.extracted_recipe
            compact_lines.append(
                f"Source {i} [{m.match_type.value.upper()} - {m.relevance_score}]: {m.title} ({m.url})\n"
                f"  Equipment: {r.get('dripper') or 'not stated'}, Dose: {r.get('dose_g')}g, Water: {r.get('water_g')}g, "
                f"Ratio: {r.get('ratio') or 'not stated'}, "
                f"Temp: {str(r.get('water_temperature_c')) + '°C' if r.get('water_temperature_c') else 'not stated'}, "
                f"Grind: {r.get('grind_description') or 'not stated'}\n"
                f"  Relevance: {', '.join(m.match_reasons) if m.match_reasons else 'General pour-over'}"
            )

        compact_context = "\n".join(compact_lines)

        return EvidencePackage(
            match_outcome=outcome,
            matched_recipes=sorted_matches[:5],
            conflicts=conflicts,
            coverage_summary=coverage,
            compact_context=compact_context,
            discovery_status=discovery_status,
            discovery_message=discovery_message,
            urls_searched=urls_searched,
            recipes_discovered=recipes_discovered
        )

    @classmethod
    def _detect_conflicts(cls, top_matches: List[ScoredMatch]) -> List[ParameterConflict]:
        conflicts = []
        if len(top_matches) < 2:
            return conflicts

        # Check water temperature disagreement (> 4°C difference)
        temps = [
            (m.title, m.extracted_recipe.get("water_temperature_c"))
            for m in top_matches
            if m.extracted_recipe.get("water_temperature_c")
        ]
        if len(temps) >= 2:
            min_temp = min(temps, key=lambda x: x[1])
            max_temp = max(temps, key=lambda x: x[1])
            diff = max_temp[1] - min_temp[1]
            if diff >= 5:
                conflicts.append(
                    ParameterConflict(
                        parameter="Water Temperature",
                        difference=f"{min_temp[0]} recommends {min_temp[1]}°C whereas {max_temp[0]} recommends {max_temp[1]}°C ({diff}°C difference)",
                        sources_involved=[min_temp[0], max_temp[0]],
                        resolution_guidance="Favor the temperature aligning with roast development: higher for light roast florals, lower for medium/dark sweetness."
                    )
                )

        # Check ratio disagreement (> 1.2 difference)
        def parse_ratio(ratio_str: str) -> Optional[float]:
            try:
                if ":" in ratio_str:
                    return float(ratio_str.split(":")[-1])
            except Exception:
                return None
            return None

        ratios = [
            (m.title, parse_ratio(m.extracted_recipe.get("ratio") or ""))
            for m in top_matches
        ]
        valid_ratios = [(t, r) for t, r in ratios if r is not None]
        if len(valid_ratios) >= 2:
            min_r = min(valid_ratios, key=lambda x: x[1])
            max_r = max(valid_ratios, key=lambda x: x[1])
            if (max_r[1] - min_r[1]) >= 1.2:
                conflicts.append(
                    ParameterConflict(
                        parameter="Brew Ratio",
                        difference=f"{min_r[0]} uses 1:{min_r[1]} while {max_r[0]} uses 1:{max_r[1]}",
                        sources_involved=[min_r[0], max_r[0]],
                        resolution_guidance="Use 1:16 as optimal balance for standard pour-over extraction clarity."
                    )
                )

        return conflicts
