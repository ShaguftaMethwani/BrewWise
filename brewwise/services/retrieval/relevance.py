from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from brewwise.schemas.coffee_profile import CoffeeProfileDraft
from brewwise.models.recipe_source import RecipeSourceModel


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

        # Check Exact / Strong match
        brand_match = p_brand and (p_brand in s_brand or s_brand in p_brand)
        estate_match = p_estate and (p_estate in s_estate or s_estate in p_estate)
        prod_in_title = p_prod and p_prod in title_str

        if estate_match and brand_match:
            score += 0.55
            reasons.append(f"Identical estate ({meta.get('estate')}) & roaster ({meta.get('brand')})")
        elif estate_match:
            score += 0.45
            reasons.append(f"Same estate/farm ({meta.get('estate')})")
        elif prod_in_title and brand_match:
            score += 0.48
            reasons.append(f"Exact product match ({profile.product_name.value})")

        # Process match
        if p_process and s_process and (p_process in s_process or s_process in p_process):
            score += 0.15
            reasons.append(f"Matching {meta.get('process')} process")

        # Origin / Country match
        if p_country and s_country and (p_country in s_country or s_country in p_country):
            score += 0.12
            reasons.append(f"Origin match: {meta.get('country')}")

        # Roast level match
        if p_roast and s_roast:
            if p_roast in s_roast or s_roast in p_roast:
                score += 0.08
                reasons.append(f"Matching {meta.get('roast_level')} roast")

        # Dripper / Equipment alignment
        if target_dripper and dripper_str and target_dripper.lower() in dripper_str:
            score += 0.08
            reasons.append(f"Matching {target_dripper} dripper")

        # Cap score at 1.0
        final_score = min(round(score, 3), 1.0)

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
            match_reasons=reasons
        )
