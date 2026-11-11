import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from brewwise.models.recipe_source import RecipeSourceModel
from brewwise.services.ingestion.scrapers.base import ScraperProvider, HttpScraper, RawContent
from brewwise.services.ingestion.deduplicator import Deduplicator
from brewwise.services.ingestion.parser import RecipeParser, ExtractedSourceRecipe
from brewwise.services.ingestion.indexer import Indexer
from brewwise.providers.embeddings.base import EmbeddingProvider
from brewwise.providers.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        llm_provider: Optional[LLMProvider] = None,
        scraper: Optional[ScraperProvider] = None
    ):
        self.scraper = scraper or HttpScraper()
        self.parser = RecipeParser(llm_provider=llm_provider)
        self.indexer = Indexer(embedding_provider=embedding_provider)

    async def ingest_url(
        self,
        url: str,
        db: AsyncSession,
        extraction_method: str = "web_crawler"
    ) -> Optional[RecipeSourceModel]:
        """Fetches, deduplicates, parses, and indexes a single recipe URL."""
        try:
            raw = await self.scraper.fetch(url)
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

        content_hash = Deduplicator.compute_content_hash(raw.content)
        existing = await Deduplicator.find_existing(content_hash, url, db)
        if existing:
            logger.info(f"Source already exists: {url}")
            return existing

        recipe = await self.parser.parse(raw.content, url)
        indexed = await self.indexer.index_source(
            url=url,
            title=raw.title,
            author=raw.author,
            site_name=url.split("//")[-1].split("/")[0],
            raw_content=raw.content,
            content_hash=content_hash,
            recipe=recipe,
            coffee_metadata=None,
            db=db,
            extraction_method=extraction_method
        )
        return indexed

    async def ingest_direct(
        self,
        url: str,
        title: str,
        author: str,
        raw_content: str,
        recipe: ExtractedSourceRecipe,
        coffee_metadata: dict,
        db: AsyncSession,
        extraction_method: str = "curated"
    ) -> RecipeSourceModel:
        """Ingests structured recipe data directly (e.g. from curated dataset)."""
        content_hash = Deduplicator.compute_content_hash(raw_content)
        existing = await Deduplicator.find_existing(content_hash, url, db)
        if existing:
            return existing

        indexed = await self.indexer.index_source(
            url=url,
            title=title,
            author=author,
            site_name=url.split("//")[-1].split("/")[0] if "//" in url else "brewwise-curated",
            raw_content=raw_content,
            content_hash=content_hash,
            recipe=recipe,
            coffee_metadata=coffee_metadata,
            db=db,
            extraction_method=extraction_method
        )
        return indexed
