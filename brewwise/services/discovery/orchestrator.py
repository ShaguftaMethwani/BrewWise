import asyncio
import hashlib
import json
import logging
import time
from collections import deque
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from brewwise.config import settings
from brewwise.models.recipe_source import RecipeSourceModel
from brewwise.schemas.coffee_profile import CoffeeProfileDraft
from brewwise.providers.search.base import SearchProvider, SearchResult
from brewwise.providers.cache.base import CacheProvider
from brewwise.providers.embeddings.base import EmbeddingProvider
from brewwise.services.discovery.page_fetcher import PageFetcher
from brewwise.services.discovery.recipe_extractor import LiveRecipeExtractor, DiscoveredRecipe
from brewwise.services.ingestion.indexer import Indexer
from brewwise.services.ingestion.parser import ExtractedSourceRecipe
from brewwise.services.ingestion.deduplicator import Deduplicator

logger = logging.getLogger(__name__)

SearchStatusType = Literal[
    "skipped_sufficient_kb",
    "success",
    "partial",
    "failed",
    "disabled"
]


class LiveDiscoveryResult(BaseModel):
    search_status: SearchStatusType
    message: str
    discovered_recipes: List[DiscoveredRecipe] = Field(default_factory=list)
    urls_attempted: int = 0
    urls_yielded_recipes: int = 0
    errors: List[str] = Field(default_factory=list)


NO_RESULTS_MESSAGE = (
    "No matching recipes were found in online sources for this coffee. "
    "This does not mean none exist — it means none were found in this search."
)

# Timestamps of recent outbound search calls, shared across requests (process-wide rate limit)
_search_call_times: deque = deque()


def _rate_limit_allows() -> bool:
    now = time.monotonic()
    while _search_call_times and now - _search_call_times[0] > 60:
        _search_call_times.popleft()
    if len(_search_call_times) >= settings.LIVE_DISCOVERY_RATE_LIMIT:
        return False
    _search_call_times.append(now)
    return True


def _join_unique(*parts: str) -> str:
    """Joins query parts, dropping words already present (e.g. estate repeated in the product name)."""
    seen, words = set(), []
    for part in parts:
        for word in (part or "").split():
            if word.lower() not in seen:
                seen.add(word.lower())
                words.append(word)
    return " ".join(words)


class DiscoveryOrchestrator:
    def __init__(
        self,
        search_provider: Optional[SearchProvider] = None,
        page_fetcher: Optional[PageFetcher] = None,
        recipe_extractor: Optional[LiveRecipeExtractor] = None,
        indexer: Optional[Indexer] = None,
        cache_provider: Optional[CacheProvider] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        llm_provider=None
    ):
        self.search_provider = search_provider
        self.page_fetcher = page_fetcher or PageFetcher(timeout=settings.LIVE_DISCOVERY_PER_URL_TIMEOUT)
        self.recipe_extractor = recipe_extractor or LiveRecipeExtractor(
            llm_provider=llm_provider, cache_provider=cache_provider, model_name=settings.LLM_MODEL
        )
        self.indexer = indexer or (Indexer(embedding_provider=embedding_provider) if embedding_provider else None)
        self.cache_provider = cache_provider
        self.total_timeout = settings.LIVE_DISCOVERY_TOTAL_TIMEOUT

    @staticmethod
    def _query_cache_key(query: str) -> str:
        q_hash = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()
        return f"cache:search_query:{q_hash}"

    async def discover(
        self,
        profile: CoffeeProfileDraft,
        db: AsyncSession,
        kb_matches_count: int = 0,
        kb_top_score: float = 0.0
    ) -> LiveDiscoveryResult:
        """Executes the full live web discovery pipeline with smart skip, timeout enforcement, and deduplication."""
        # Check if live discovery is disabled
        if not settings.LIVE_DISCOVERY_ENABLED or not self.search_provider:
            return LiveDiscoveryResult(
                search_status="disabled",
                message=(
                    "Live web search is not configured, so no online sources were checked. "
                    "Results are from the local knowledge base only."
                )
            )

        # 1. Skip rule: only when the KB already holds an exact match for this coffee
        #    (a coffee that is not pre-indexed always triggers a live search)
        if kb_matches_count >= 3 and kb_top_score >= settings.LIVE_DISCOVERY_SKIP_SCORE:
            logger.info(f"Skipping live discovery: KB already has {kb_matches_count} strong matches (top score {kb_top_score})")
            return LiveDiscoveryResult(
                search_status="skipped_sufficient_kb",
                message="Found expert recipes in the BrewWise Knowledge Base"
            )

        # 2. Build search queries
        brand = profile.brand.value or ""
        estate = profile.estate.value or ""
        name = profile.product_name.value or ""
        process = profile.process.value or ""
        country = profile.country.value or ""

        query_primary = _join_unique(brand, estate, name, process.replace("_", " "), "pour-over recipe")
        query_fallback = _join_unique(estate or brand, country, process.replace("_", " "), "V60 brew guide")

        # Enforce total timeout budget
        try:
            return await asyncio.wait_for(
                self._execute_discovery(query_primary, query_fallback, profile, db),
                timeout=self.total_timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Live discovery exceeded total timeout budget ({self.total_timeout}s). Returning partial.")
            return LiveDiscoveryResult(
                search_status="partial",
                message="Online search timed out before processing all candidate pages.",
                errors=["Total timeout budget exceeded"]
            )
        except Exception as e:
            logger.error(f"Live discovery failed with unexpected error: {e}")
            return LiveDiscoveryResult(
                search_status="failed",
                message="Online recipe search was unavailable. Results are based on the existing knowledge base only.",
                errors=[str(e)]
            )

    async def _execute_discovery(
        self,
        primary_query: str,
        fallback_query: str,
        profile: CoffeeProfileDraft,
        db: AsyncSession
    ) -> LiveDiscoveryResult:
        # Check 1-hour Redis search cache
        search_results: List[SearchResult] = []
        cache_key = self._query_cache_key(primary_query)

        if self.cache_provider:
            try:
                cached_json = await self.cache_provider.get(cache_key)
                if cached_json:
                    raw_items = json.loads(cached_json)
                    search_results = [SearchResult(**item) for item in raw_items]
            except Exception:
                pass

        # Call SearchProvider if not cached
        if not search_results:
            if not _rate_limit_allows():
                return LiveDiscoveryResult(
                    search_status="failed",
                    message="Online recipe search is temporarily rate-limited. Results are based on the existing knowledge base only.",
                    errors=["Search rate limit reached"]
                )
            try:
                search_results = await self.search_provider.search(
                    query=primary_query,
                    max_results=settings.LIVE_DISCOVERY_MAX_URLS
                )
            except Exception as e:
                logger.warning(f"Search API failed on primary query: {e}")
                return LiveDiscoveryResult(
                    search_status="failed",
                    message="Online recipe search was unavailable. Results are based on the existing knowledge base only.",
                    errors=[str(e)]
                )

            # Try fallback query if primary returned 0 results
            if not search_results and fallback_query and fallback_query != primary_query:
                try:
                    search_results = await self.search_provider.search(
                        query=fallback_query,
                        max_results=settings.LIVE_DISCOVERY_MAX_URLS
                    )
                except Exception:
                    pass

            # Cache query results in Redis for 1 hour (3600 seconds)
            if search_results and self.cache_provider:
                try:
                    dumped = json.dumps([r.model_dump() for r in search_results])
                    await self.cache_provider.set(cache_key, dumped, ttl_seconds=3600)
                except Exception:
                    pass

        if not search_results:
            return LiveDiscoveryResult(
                search_status="success",
                message=NO_RESULTS_MESSAGE,
                urls_attempted=0,
                urls_yielded_recipes=0
            )

        # 3. Filter URLs: Skip URLs already indexed in database
        candidate_urls = list(dict.fromkeys(
            r.url for r in search_results if r.url and r.url.startswith(("http://", "https://"))
        ))
        existing_stmt = select(RecipeSourceModel.url).where(RecipeSourceModel.url.in_(candidate_urls))
        res = await db.execute(existing_stmt)
        already_indexed = set(res.scalars().all())

        urls_to_fetch = [u for u in candidate_urls if u not in already_indexed][:settings.LIVE_DISCOVERY_MAX_URLS]

        if not urls_to_fetch:
            # All returned URLs were already present in the knowledge base
            return LiveDiscoveryResult(
                search_status="skipped_sufficient_kb",
                message="Online search only returned pages that are already in the knowledge base.",
                urls_attempted=len(candidate_urls),
                urls_yielded_recipes=len(already_indexed)
            )

        # 4. Fetch pages in parallel with per-URL timeout
        fetch_tasks = [self.page_fetcher.fetch(url) for url in urls_to_fetch]
        fetched_pages_raw = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        valid_pages = [p for p in fetched_pages_raw if p and not isinstance(p, Exception)]

        if not valid_pages:
            return LiveDiscoveryResult(
                search_status="partial",
                message=(
                    f"Online search found {len(urls_to_fetch)} candidate page(s), but none could be read "
                    "(blocked, access-restricted, or timed out). No online recipes could be verified."
                ),
                urls_attempted=len(urls_to_fetch),
                urls_yielded_recipes=0
            )

        # 5. Batched recipe extraction (1 LLM call)
        discovered_recipes = await self.recipe_extractor.extract_batch(valid_pages)

        # 6. Optionally persist discovered recipes into KB
        if settings.LIVE_DISCOVERY_PERSIST and self.indexer and discovered_recipes:
            for disc in discovered_recipes:
                try:
                    content_hash = Deduplicator.compute_content_hash(disc.instructions or disc.title)
                    existing = await Deduplicator.find_existing(content_hash, disc.url, db)
                    if not existing:
                        recipe_struct = ExtractedSourceRecipe(
                            dripper=disc.dripper,
                            dose_g=disc.dose_g,
                            water_g=disc.water_g,
                            ratio=disc.ratio,
                            water_temperature_c=disc.water_temperature_c,
                            grind_description=disc.grind_description,
                            instructions=disc.instructions,
                            bloom_time_seconds=None,
                            target_brew_time_seconds=None,
                            brand=disc.coffee_metadata.get("brand"),
                            estate=disc.coffee_metadata.get("estate"),
                            country=disc.coffee_metadata.get("country"),
                            process=disc.coffee_metadata.get("process"),
                            roast_level=disc.coffee_metadata.get("roast_level")
                        )
                        await self.indexer.index_source(
                            url=disc.url,
                            title=disc.title,
                            author=disc.author,
                            site_name=disc.site_name,
                            raw_content=disc.instructions or f"Discovered live pour-over recipe: {disc.title}",
                            content_hash=content_hash,
                            recipe=recipe_struct,
                            coffee_metadata=disc.coffee_metadata,
                            db=db,
                            extraction_method="live_search",
                            discovery_context=primary_query
                        )
                except Exception as e:
                    logger.warning(f"Failed to persist discovered source {disc.url}: {e}")

        recipe_count = len(discovered_recipes)
        if recipe_count > 0:
            msg = f"Found {recipe_count} recipe(s) from online sources"
        else:
            msg = (
                f"Checked {len(valid_pages)} online page(s) but none contained a usable pour-over recipe. "
                "This does not mean none exist — it means none were found in this search."
            )

        return LiveDiscoveryResult(
            search_status="success",
            message=msg,
            discovered_recipes=discovered_recipes,
            urls_attempted=len(urls_to_fetch),
            urls_yielded_recipes=recipe_count
        )
