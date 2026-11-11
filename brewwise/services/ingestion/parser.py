import re
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from brewwise.providers.llm.base import LLMProvider


class ExtractedSourceRecipe(BaseModel):
    dripper: str = Field(default="Hario V60")
    dose_g: float = Field(default=15.0)
    water_g: float = Field(default=240.0)
    ratio: str = Field(default="1:16")
    water_temperature_c: int = Field(default=93)
    grind_description: str = Field(default="Medium-fine")
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

        # Dripper detection
        dripper = "Hario V60"
        if "kalita" in lower:
            dripper = "Kalita Wave"
        elif "origami" in lower:
            dripper = "Origami Dripper"
        elif "chemex" in lower:
            dripper = "Chemex"
        elif "aeropress" in lower:
            dripper = "AeroPress"
        elif "clever" in lower:
            dripper = "Clever Dripper"
        elif "fellow" in lower or "stagg" in lower:
            dripper = "Fellow Stagg [X]"

        # Dose detection (e.g. 15g, 18 grams, Dose: 16g)
        dose = 15.0
        dose_m = re.search(r"(?:dose|coffee|grounds?)[:\s]*(\d{1,2}(?:\.\d)?)\s*(?:g|grams)", lower)
        if dose_m:
            dose = float(dose_m.group(1))

        # Water detection (e.g. 240g, 250 ml, Water: 300g)
        water = dose * 16.0
        water_m = re.search(r"(?:water|yield|total)[:\s]*(\d{2,3}(?:\.\d)?)\s*(?:g|ml|grams)", lower)
        if water_m:
            water = float(water_m.group(1))

        # Ratio detection (e.g. 1:16, 1:15)
        ratio = f"1:{round(water / dose, 1)}" if dose > 0 else "1:16"
        ratio_m = re.search(r"1\s*:\s*(\d{1,2}(?:\.\d)?)", lower)
        if ratio_m:
            ratio = f"1:{ratio_m.group(1)}"

        # Temperature detection (e.g. 93°C, 92C, 205°F)
        temp = 93
        temp_c_m = re.search(r"(\d{2})\s*(?:°\s*c|celsius|c\b)", lower)
        if temp_c_m:
            val = int(temp_c_m.group(1))
            if 80 <= val <= 99:
                temp = val
        else:
            temp_f_m = re.search(r"(\d{3})\s*(?:°\s*f|fahrenheit|f\b)", lower)
            if temp_f_m:
                val_f = int(temp_f_m.group(1))
                if 175 <= val_f <= 212:
                    temp = round((val_f - 32) * 5 / 9)

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

        # Grind detection
        grind = "Medium-fine"
        if "medium-coarse" in lower or "coarse" in lower:
            grind = "Medium-coarse"
        elif "fine" in lower:
            grind = "Fine"
        elif "medium" in lower:
            grind = "Medium"

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
