import hashlib
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from jinja2 import Template
from pydantic import BaseModel, Field

from brewwise.providers.llm.base import LLMProvider
from brewwise.providers.cache.base import CacheProvider
from brewwise.services.ingestion.scrapers.base import RawContent
from brewwise.services.ingestion.parser import RecipeParser

logger = logging.getLogger(__name__)


class DiscoveredRecipe(BaseModel):
    url: str
    has_recipe: bool = Field(default=True, description="Whether the page contains an actual pour-over recipe")
    title: str = Field(default="Discovered Recipe")
    author: Optional[str] = None
    site_name: Optional[str] = None
    dripper: str = Field(default="Hario V60")
    dose_g: float = Field(default=15.0)
    water_g: float = Field(default=240.0)
    ratio: str = Field(default="1:16")
    water_temperature_c: int = Field(default=93)
    grind_description: str = Field(default="Medium-fine")
    coffee_metadata: Dict[str, Any] = Field(default_factory=dict)
    instructions: Optional[str] = None


class DiscoveredRecipeBatch(BaseModel):
    recipes: List[DiscoveredRecipe] = Field(default_factory=list)


class LiveRecipeExtractor:
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        cache_provider: Optional[CacheProvider] = None,
        model_name: str = "gemini-2.5-flash"
    ):
        self.llm_provider = llm_provider
        self.cache_provider = cache_provider
        self.model_name = model_name
        self.rule_parser = RecipeParser()

        template_path = Path(__file__).parent.parent.parent / "prompts" / "v1" / "extract_web_recipes_batch.j2"
        if template_path.exists():
            self.template = Template(template_path.read_text(encoding="utf-8"))
        else:
            self.template = None

    @staticmethod
    def _url_cache_key(url: str) -> str:
        url_hash = hashlib.sha256(url.strip().encode("utf-8")).hexdigest()
        return f"cache:discovered_recipe:{url_hash}"

    async def extract_batch(self, pages: List[RawContent]) -> List[DiscoveredRecipe]:
        """Extracts recipes from multiple pages using 30-day Redis cache + a single batched Gemini call."""
        if not pages:
            return []

        results: List[DiscoveredRecipe] = []
        uncached_pages: List[RawContent] = []

        # 1. Check Redis cache for each URL (30-day cache)
        for page in pages:
            cache_key = self._url_cache_key(page.url)
            cached_data = None
            if self.cache_provider:
                try:
                    cached_data = await self.cache_provider.get(cache_key)
                except Exception as e:
                    logger.debug(f"Cache get failed: {e}")

            if cached_data:
                try:
                    discovered = DiscoveredRecipe.model_validate_json(cached_data)
                    if discovered.has_recipe:
                        results.append(discovered)
                    continue
                except Exception:
                    pass

            uncached_pages.append(page)

        if not uncached_pages:
            return results

        # 2. Batch extraction for uncached pages in a single LLM call
        batch_extracted: List[DiscoveredRecipe] = []

        if self.llm_provider and self.template:
            try:
                prompt = self.template.render(pages=uncached_pages)
                response = await self.llm_provider.generate_structured(
                    prompt=prompt,
                    response_schema=DiscoveredRecipeBatch,
                    system_instruction="You are an expert barista extracting exact pour-over recipes. Discard non-pour-over methods.",
                    model=self.model_name
                )
                if response and response.recipes:
                    batch_extracted = response.recipes
            except Exception as e:
                logger.warning(f"Batched LLM extraction failed, using rule-based fallback: {e}")

        # 3. Rule-based fallback for any pages not extracted
        extracted_urls = {r.url for r in batch_extracted}
        for page in uncached_pages:
            if page.url not in extracted_urls:
                # Rule-based fallback
                rule_res = self.rule_parser._rule_based_parse(page.content, page.url)
                # Check if text actually resembles a pour-over recipe
                lower = page.content.lower()
                has_recipe = any(k in lower for k in ["pour-over", "v60", "kalita", "origami", "ratio", "bloom", "drawdown"])
                discovered = DiscoveredRecipe(
                    url=page.url,
                    has_recipe=has_recipe,
                    title=page.title or f"{rule_res.dripper} Recipe",
                    author=page.author,
                    site_name=page.url.split("//")[-1].split("/")[0],
                    dripper=rule_res.dripper,
                    dose_g=rule_res.dose_g,
                    water_g=rule_res.water_g,
                    ratio=rule_res.ratio,
                    water_temperature_c=rule_res.water_temperature_c,
                    grind_description=rule_res.grind_description,
                    coffee_metadata={
                        "brand": rule_res.brand,
                        "estate": rule_res.estate,
                        "country": rule_res.country,
                        "process": rule_res.process,
                        "roast_level": rule_res.roast_level,
                    },
                    instructions=rule_res.instructions
                )
                batch_extracted.append(discovered)

        # 4. Filter and cache all extracted recipes (30-day TTL = 2,592,000s)
        for disc in batch_extracted:
            cache_key = self._url_cache_key(disc.url)
            if self.cache_provider:
                try:
                    await self.cache_provider.set(cache_key, disc.model_dump_json(), ttl_seconds=2592000)
                except Exception:
                    pass

            if disc.has_recipe and disc.dose_g > 0 and disc.water_g > 0:
                results.append(disc)

        return results
