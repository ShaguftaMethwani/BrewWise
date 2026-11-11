import asyncio
import json
import logging
from pathlib import Path

from brewwise.config import settings
from brewwise.db.session import AsyncSessionLocal, init_db
from brewwise.providers.embeddings.gemini_embed import GeminiEmbeddingProvider
from brewwise.services.ingestion.pipeline import IngestionPipeline
from brewwise.services.ingestion.parser import ExtractedSourceRecipe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_curated_knowledge_base():
    """Seeds the curated knowledge base into the database if empty."""
    json_path = Path(__file__).parent.parent / "data" / "curated_sources.json"
    if not json_path.exists():
        logger.warning(f"Curated sources file not found at {json_path}")
        return 0

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    embed_provider = GeminiEmbeddingProvider(
        api_key=settings.GOOGLE_API_KEY,
        model=settings.EMBEDDING_MODEL
    )
    pipeline = IngestionPipeline(embedding_provider=embed_provider)

    count = 0
    async with AsyncSessionLocal() as session:
        for item in data:
            recipe = ExtractedSourceRecipe(
                dripper=item["dripper"],
                dose_g=item["dose_g"],
                water_g=item["water_g"],
                ratio=item["ratio"],
                water_temperature_c=item["water_temperature_c"],
                grind_description=item["grind_description"],
                bloom_water_g=item["bloom_water_g"],
                bloom_time_seconds=item["bloom_time_seconds"],
                target_brew_time_seconds=item["target_brew_time_seconds"],
                brand=item["coffee_metadata"].get("brand"),
                estate=item["coffee_metadata"].get("estate"),
                country=item["coffee_metadata"].get("country"),
                region=item["coffee_metadata"].get("region"),
                process=item["coffee_metadata"].get("process"),
                roast_level=item["coffee_metadata"].get("roast_level"),
                varietal=item["coffee_metadata"].get("varietal"),
                tasting_notes=item["coffee_metadata"].get("tasting_notes"),
            )

            res = await pipeline.ingest_direct(
                url=item["url"],
                title=item["title"],
                author=item["author"],
                raw_content=item["raw_content"],
                recipe=recipe,
                coffee_metadata=item["coffee_metadata"],
                db=session,
                extraction_method="curated"
            )
            if res:
                count += 1

    logger.info(f"Knowledge base populated with {count} curated recipes.")
    return count


if __name__ == "__main__":
    async def main():
        await init_db()
        await seed_curated_knowledge_base()

    asyncio.run(main())
