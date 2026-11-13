import re
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from brewwise.providers.llm.base import LLMProvider


class ExtractedSourceRecipe(BaseModel):
    dripper: Optional[str] = Field(default="Hario V60")
    dose_g: float = Field(default=15.0)
    water_g: float = Field(default=240.0)
    ratio: Optional[str] = Field(default="1:16")
    water_temperature_c: Optional[int] = Field(default=93)
    grind_description: Optional[str] = Field(default="Medium-fine")
    bloom_water_g: Optional[float] = None
    bloom_time_seconds: Optional[int] = 45
    target_brew_time_seconds: Optional[int] = 180
    instructions: Optional[str] = None

    # Coffee identity
    brand: Optional[str] = None
    estate: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    process: Optional[str] = None
    roast_level: Optional[str] = None
    varietal: Optional[str] = None
    tasting_notes: Optional[str] = None


_NUM = r"(\d{1,3}(?:\.\d)?)"
_G = r"\s*(?:g|gr|grams?)\b"
_ML = r"\s*(?:g|gr|grams?|ml)\b"


def extract_observed_parameters(text: str) -> Dict[str, Any]:
    """Extracts only the brewing parameters explicitly stated in the text.

    Nothing is defaulted: a key is present only when the value was actually found,
    so callers can tell a real recipe from a page that merely mentions coffee.
    """
    lower = (text or "").lower()
    found: Dict[str, Any] = {}

    for needle, name in [
        ("v60", "Hario V60"), ("kalita", "Kalita Wave"), ("origami", "Origami Dripper"),
        ("chemex", "Chemex"), ("aeropress", "AeroPress"), ("clever", "Clever Dripper"),
        ("stagg", "Fellow Stagg [X]"), ("april brewer", "April Brewer"),
    ]:
        if needle in lower:
            found["dripper"] = name
            break

    dose_m = (
        re.search(rf"(?:dose|coffee|grounds?)\s*[:\-]?\s*{_NUM}{_G}", lower)
        or re.search(rf"{_NUM}{_G}\s*(?:of\s+)?(?:ground\s+|fresh(?:ly)?\s+ground\s+)?(?:coffee|dose|beans|grounds)", lower)
    )
    if dose_m:
        dose = float(dose_m.group(1))
        if 5 <= dose <= 60:
            found["dose_g"] = dose

    water_m = (
        re.search(rf"(?:water|yield|total(?:\s+water)?|brew\s+weight)\s*[:\-]?\s*{_NUM}{_ML}", lower)
        or re.search(rf"{_NUM}{_ML}\s*(?:of\s+)?(?:hot\s+|filtered\s+|total\s+)?water", lower)
    )
    if water_m:
        water = float(water_m.group(1))
        if 80 <= water <= 1000:
            found["water_g"] = water

    ratio_m = re.search(r"\b1\s*:\s*(\d{1,2}(?:\.\d)?)\b", lower)
    if ratio_m and 10 <= float(ratio_m.group(1)) <= 20:
        found["ratio"] = f"1:{ratio_m.group(1)}"

    # Derive the missing one of dose / water / ratio only from the two that were stated
    if "dose_g" in found and "water_g" not in found and "ratio" in found:
        found["water_g"] = round(found["dose_g"] * float(found["ratio"].split(":")[1]), 1)
    if "dose_g" in found and "water_g" in found and "ratio" not in found:
        found["ratio"] = f"1:{round(found['water_g'] / found['dose_g'], 1)}"

    temp_c_m = re.search(r"(\d{2})\s*(?:°\s*c\b|degrees\s+c|celsius|c\b)", lower)
    if temp_c_m and 80 <= int(temp_c_m.group(1)) <= 100:
        found["water_temperature_c"] = int(temp_c_m.group(1))
    else:
        temp_f_m = re.search(r"(\d{3})\s*(?:°\s*f\b|degrees\s+f|fahrenheit|f\b)", lower)
        if temp_f_m and 175 <= int(temp_f_m.group(1)) <= 212:
            found["water_temperature_c"] = round((int(temp_f_m.group(1)) - 32) * 5 / 9)

    grind_m = re.search(r"(medium[\s-]coarse|medium[\s-]fine|coarse|fine|medium)\s*(?:grind|ground)|grind(?:\s+size)?\s*[:\-]?\s*(medium[\s-]coarse|medium[\s-]fine|coarse|fine|medium)", lower)
    if grind_m:
        found["grind_description"] = (grind_m.group(1) or grind_m.group(2)).replace(" ", "-").capitalize()

    return found


class RecipeParser:
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider

    async def parse(self, text: str, url: str = "") -> ExtractedSourceRecipe:
        """Parses recipe text using rule heuristics with optional LLM enhancement."""
        # 1. First run regex/rule extractor for fast reliable parameter discovery
        recipe = self._rule_based_parse(text, url)

        # 2. If LLM is available and text is long or ambiguous, enhance extraction
        if self.llm_provider and len(text) > 80:
            try:
                prompt = (
                    f"Extract the pour-over brewing recipe and coffee identity details from this text.\n"
                    f"URL: {url}\n\n"
                    f"TEXT:\n{text[:2000]}\n\n"
                    f"Ensure exact extraction of dripper, dose_g, water_g, ratio, temperature in Celsius, grind, process, origin, roast."
                )
                llm_recipe = await self.llm_provider.generate_structured(
                    prompt=prompt,
                    response_schema=ExtractedSourceRecipe,
                    system_instruction="You are an expert barista extracting exact recipe and coffee parameters from articles."
                )
                if llm_recipe and llm_recipe.dose_g > 0 and llm_recipe.water_g > 0:
                    return llm_recipe
            except Exception:
                pass

        return recipe

    def _rule_based_parse(self, text: str, url: str = "") -> ExtractedSourceRecipe:
        lower = text.lower()
        observed = extract_observed_parameters(text)

        # Values not stated in the text fall back to conventional defaults. Callers that
        # must not invent parameters (live discovery) use extract_observed_parameters directly.
        dripper = observed.get("dripper") or "Hario V60"
        dose = observed.get("dose_g") or 15.0
        water = observed.get("water_g") or dose * 16.0
        ratio = observed.get("ratio") or (f"1:{round(water / dose, 1)}" if dose > 0 else "1:16")
        temp = observed.get("water_temperature_c") or 93
        grind = observed.get("grind_description") or "Medium-fine"

        # Process detection
        process = None
        for p in ["anaerobic", "honey", "natural", "washed", "monsooned"]:
            if p in lower:
                process = p.capitalize()
                break

        # Roast detection
        roast = None
        for r in ["light-medium", "light", "medium-dark", "medium", "dark"]:
            if r in lower:
                roast = r.capitalize()
                break

        # Origin / Country detection
        country = None
        for c in ["India", "Ethiopia", "Colombia", "Kenya", "Guatemala", "Costa Rica", "Rwanda", "Brazil", "Panama", "Yemen", "Indonesia", "Burundi"]:
            if c.lower() in lower:
                country = c
                break

        return ExtractedSourceRecipe(
            dripper=dripper,
            dose_g=dose,
            water_g=water,
            ratio=ratio,
            water_temperature_c=temp,
            grind_description=grind,
            bloom_water_g=round(dose * 3.0, 1),
            bloom_time_seconds=45,
            target_brew_time_seconds=180,
            instructions=text[:500] if text else None,
            country=country,
            process=process,
            roast_level=roast
        )
