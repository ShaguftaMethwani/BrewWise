from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from brewwise.schemas.coffee_profile import CoffeeProfileDraft
from brewwise.models.recipe_source import RecipeSourceModel
from brewwise.services.identity.normaliser import normalise_process_method


def _same(a: str, b: str) -> bool:
    """True only when both values are known and one contains the other."""
    return bool(a) and bool(b) and (a in b or b in a)


class MatchClassification(str, Enum):
    EXACT = "exact"
    STRONG = "strong"
    RELATED = "related"
    ANALOGOUS = "analogous"
    GENERAL = "general"


class ScoredMatch(BaseModel):
    source_id: str
    url: str
    title: str
    author: Optional[str] = None
    site_name: Optional[str] = None
    match_type: MatchClassification
    relevance_score: float
    coffee_metadata: Dict[str, Any] = Field(default_factory=dict)
    extracted_recipe: Dict[str, Any] = Field(default_factory=dict)
    match_reasons: list[str] = Field(default_factory=list)
    is_live_discovered: bool = False



class MatchClassifier:
    EXACT_THRESHOLD = 0.92
    STRONG_THRESHOLD = 0.85
    RELATED_THRESHOLD = 0.70
    ANALOGOUS_THRESHOLD = 0.55

    @classmethod
    def score_and_classify(
        cls,
        source: RecipeSourceModel,
        profile: CoffeeProfileDraft,
        target_dripper: Optional[str] = "Hario V60",
        base_retrieval_score: float = 0.0
    ) -> Optional[ScoredMatch]:
        """Calculates fine-grained relevance score and assigns match classification."""
        recipe_dict = source.extracted_recipe or {}
        meta = source.coffee_metadata or {}

        # 1. Filter out non-pour-over methods
        dripper_str = (recipe_dict.get("dripper") or "").lower()
        title_str = (source.title or "").lower()
        content_str = (source.raw_content or "").lower()

        is_pour_over = any(
            d in dripper_str or d in title_str or d in content_str
            for d in ["v60", "kalita", "origami", "chemex", "dripper", "pour-over", "pour over", "filter", "aeropress", "clever"]
        )
        if not is_pour_over:
            return None

        # Verify recipe completeness (must have dose and water)
        dose = recipe_dict.get("dose_g") or 0.0
        water = recipe_dict.get("water_g") or 0.0
        if dose <= 0 or water <= 0:
            return None

        score = 0.40  # Base score for valid pour-over recipe
        reasons = []

        # Target coffee parameters
        p_brand = (profile.brand.value or "").strip().lower()
        p_estate = (profile.estate.value or "").strip().lower()
        p_prod = (profile.product_name.value or "").strip().lower()
        p_country = (profile.country.value or "").strip().lower()
        p_process = (profile.process.value or "").strip().lower()
        p_roast = (profile.roast_level.value or "").strip().lower()

        # Source coffee parameters
        s_brand = (meta.get("brand") or "").strip().lower()
        s_estate = (meta.get("estate") or "").strip().lower()
        s_country = (meta.get("country") or "").strip().lower()
        s_process = (meta.get("process") or "").strip().lower()
        s_roast = (meta.get("roast_level") or "").strip().lower()

        s_product = (meta.get("product_name") or "").strip().lower()

        # Identity matching. Both sides must be known: a source with no brand/estate
        # metadata is "unverified", never a match.
        brand_match = _same(p_brand, s_brand)
        estate_match = _same(p_estate, s_estate)
        prod_match = bool(p_prod) and (_same(p_prod, s_product) or p_prod in title_str)

        if estate_match and brand_match:
            score += 0.55
            reasons.append(f"Identical estate ({meta.get('estate')}) & roaster ({meta.get('brand')})")
        elif estate_match:
            score += 0.45
            reasons.append(f"Same estate/farm ({meta.get('estate')})")
        elif prod_match and brand_match:
            score += 0.48
            reasons.append(f"Exact product match ({profile.product_name.value})")
        identity_match = estate_match or (prod_match and brand_match)

        # Process match (compared on normalised terminology, e.g. "Fully Washed" == "washed")
        n_p_process = (normalise_process_method(p_process) or "") if p_process else ""
        n_s_process = (normalise_process_method(s_process) or "") if s_process else ""
        process_match = _same(n_p_process, n_s_process)
        if process_match:
            score += 0.15
            reasons.append(f"Matching {meta.get('process')} process")

        # Origin / Country match
        if _same(p_country, s_country):
            score += 0.12
            reasons.append(f"Origin match: {meta.get('country')}")

        # Roast level match
        if _same(p_roast, s_roast):
            score += 0.08
            reasons.append(f"Matching {meta.get('roast_level')} roast")

        # A recipe for another lot from the same estate/roaster is a reference, not an exact match.
        score_cap = 1.0
        if identity_match:
            if n_p_process and n_s_process and not process_match:
                score_cap = cls.STRONG_THRESHOLD - 0.01
                reasons.append(
                    f"Different lot: source is {meta.get('process')} process, this coffee is "
                    f"{profile.process.value} - used as a related reference, not an exact match"
                )
            elif p_prod and s_product and not _same(p_prod, s_product) and not estate_match:
                score_cap = cls.STRONG_THRESHOLD - 0.01
                reasons.append("Same roaster but a different product - used as a related reference")
            elif estate_match and not brand_match:
                if p_brand and s_brand:
                    score_cap = cls.STRONG_THRESHOLD - 0.01
                    reasons.append(
                        f"Same estate but roasted by {meta.get('brand')} - a different release, used as a related reference"
                    )
                else:
                    # Roaster unknown on one side: cannot be verified as the exact coffee
                    score_cap = cls.EXACT_THRESHOLD - 0.01
                    reasons.append("Roaster could not be verified, so this is not confirmed as the exact coffee")

        # Dripper / Equipment alignment
        if target_dripper and dripper_str and target_dripper.lower() in dripper_str:
            score += 0.08
            reasons.append(f"Matching {target_dripper} dripper")

        # Cap score at 1.0
        final_score = round(min(score, score_cap, 1.0), 3)

        # Classification thresholds
        if final_score >= cls.EXACT_THRESHOLD:
            classification = MatchClassification.EXACT
        elif final_score >= cls.STRONG_THRESHOLD:
            classification = MatchClassification.STRONG
        elif final_score >= cls.RELATED_THRESHOLD:
            classification = MatchClassification.RELATED
        elif final_score >= cls.ANALOGOUS_THRESHOLD:
            classification = MatchClassification.ANALOGOUS
        else:
            classification = MatchClassification.GENERAL

        # Filter out anything below ANALOGOUS threshold (0.55)
        if final_score < cls.ANALOGOUS_THRESHOLD:
            return None

        return ScoredMatch(
            source_id=source.id,
            url=source.url,
            title=source.title or "Pour-Over Recipe",
            author=source.author,
            site_name=source.site_name,
            match_type=classification,
            relevance_score=final_score,
            coffee_metadata=meta,
            extracted_recipe=recipe_dict,
            match_reasons=reasons,
            is_live_discovered=(source.extraction_method == "live_search")
        )
