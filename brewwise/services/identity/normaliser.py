import re
import unicodedata
from typing import Dict, Optional
from brewwise.schemas.coffee_profile import CoffeeProfileDraft


PROCESS_MAP: Dict[str, str] = {
    "natural process": "natural",
    "natural": "natural",
    "dry process": "natural",
    "fully washed": "washed",
    "washed process": "washed",
    "washed": "washed",
    "wet process": "washed",
    "honey process": "honey",
    "honey": "honey",
    "yellow honey": "yellow_honey",
    "red honey": "red_honey",
    "black honey": "black_honey",
    "anaerobic natural": "anaerobic_natural",
    "anaerobic nat": "anaerobic_natural",
    "anaerobic washed": "anaerobic_washed",
    "anaerobic": "anaerobic",
    "carbonic maceration": "carbonic_maceration",
    "thermal shock": "thermal_shock",
    "lactic": "lactic",
}

ROAST_MAP: Dict[str, str] = {
    "light roast": "light",
    "light": "light",
    "cinnamon": "light",
    "filter roast": "light",
    "medium light": "medium_light",
    "medium-light": "medium_light",
    "medium roast": "medium",
    "medium": "medium",
    "city": "medium",
    "full city": "medium_dark",
    "medium dark": "medium_dark",
    "medium-dark": "medium_dark",
    "dark roast": "dark",
    "dark": "dark",
    "omni roast": "omni",
    "omni": "omni",
}


def clean_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    # Normalize unicode (decompose + compose canonical)
    normalized = unicodedata.normalize("NFKC", text)
    # Strip excess whitespace
    return re.sub(r"\s+", " ", normalized).strip()


def normalise_roaster_name(name: Optional[str]) -> Optional[str]:
    text = clean_text(name)
    if not text:
        return None
    pattern = r"(?i)\b(coffee roasters|specialty coffee|coffee company|coffee co\.?|roasters|coffee|co\.?)\b"
    previous = None
    cleaned = text
    while previous != cleaned:
        previous = cleaned
        cleaned = re.sub(pattern, "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -.,")
    return cleaned if cleaned else text


def normalise_process_method(process: Optional[str]) -> Optional[str]:
    text = clean_text(process)
    if not text:
        return None
    key = text.lower()
    return PROCESS_MAP.get(key, text.lower().replace(" ", "_"))


def normalise_roast_level(roast: Optional[str]) -> Optional[str]:
    text = clean_text(roast)
    if not text:
        return None
    key = text.lower()
    return ROAST_MAP.get(key, text.lower().replace(" ", "_"))


def normalise_profile(draft: CoffeeProfileDraft) -> CoffeeProfileDraft:
    """Normalises canonical fields on the draft in place and returns it."""
    if draft.brand.value:
        draft.brand.value = normalise_roaster_name(draft.brand.value)
    if draft.product_name.value:
        draft.product_name.value = clean_text(draft.product_name.value)
    if draft.estate.value:
        draft.estate.value = clean_text(draft.estate.value)
    if draft.country.value:
        draft.country.value = clean_text(draft.country.value)
    if draft.region.value:
        draft.region.value = clean_text(draft.region.value)
    if draft.varietal.value:
        draft.varietal.value = clean_text(draft.varietal.value)
    if draft.process.value:
        draft.process.value = normalise_process_method(draft.process.value)
    if draft.roast_level.value:
        draft.roast_level.value = normalise_roast_level(draft.roast_level.value)
    if draft.tasting_notes.value:
        draft.tasting_notes.value = clean_text(draft.tasting_notes.value)
    return draft
