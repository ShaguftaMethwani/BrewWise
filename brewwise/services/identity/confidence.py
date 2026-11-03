from typing import List, Optional
from brewwise.schemas.coffee_profile import CoffeeProfileDraft


def calculate_overall_confidence(draft: CoffeeProfileDraft) -> float:
    """
    Computes weighted overall confidence based on crucial fields.
    """
    weights = {
        "brand": 0.20,
        "product_name": 0.20,
        "country": 0.15,
        "process": 0.20,
        "roast_level": 0.15,
        "varietal": 0.10,
    }

    scores = [
        draft.brand.confidence * weights["brand"],
        draft.product_name.confidence * weights["product_name"],
        draft.country.confidence * weights["country"],
        draft.process.confidence * weights["process"],
        draft.roast_level.confidence * weights["roast_level"],
        draft.varietal.confidence * weights["varietal"],
    ]

    total_weight = sum(weights.values())
    return round(sum(scores) / total_weight, 2)
