import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from brewwise.models.recipe_source import RecipeSourceModel, RecipeEmbeddingModel
from brewwise.providers.embeddings.base import EmbeddingProvider
from brewwise.services.ingestion.parser import ExtractedSourceRecipe

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    """Splits text into chunks of roughly chunk_size words with overlap."""
    words = text.split()
    if not words:
        return []
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start += (chunk_size - overlap)
    return chunks


class Indexer:
    def __init__(self, embedding_provider: EmbeddingProvider):
        self.embedding_provider = embedding_provider

    async def index_source(
        self,
        url: str,
        title: Optional[str],
        author: Optional[str],
        site_name: Optional[str],
        raw_content: str,
        content_hash: str,
        recipe: ExtractedSourceRecipe,
        coffee_metadata: Optional[Dict[str, Any]],
        db: AsyncSession,
        extraction_method: str = "curated",
        discovery_context: Optional[str] = None
    ) -> RecipeSourceModel:
        # Build coffee metadata dict from recipe if not provided
        if not coffee_metadata:
            coffee_metadata = {
                "brand": recipe.brand,
                "estate": recipe.estate,
                "country": recipe.country,
                "region": recipe.region,
                "process": recipe.process,
                "roast_level": recipe.roast_level,
                "varietal": recipe.varietal,
                "tasting_notes": recipe.tasting_notes,
            }

        source = RecipeSourceModel(
            id=str(uuid.uuid4()),
            url=url,
            title=title or f"{recipe.dripper} Pour-Over Recipe",
            author=author or "Specialty Coffee Roaster",
            site_name=site_name,
            raw_content=raw_content,
            content_hash=content_hash,
            extraction_method=extraction_method,
            discovery_context=discovery_context,
            coffee_metadata=coffee_metadata,
            extracted_recipe=recipe.model_dump(mode="json"),
            is_accessible=True
        )
        db.add(source)
        await db.flush()

        # Build embedding texts: include rich semantic summary + chunks
        summary_text = (
            f"Coffee Recipe: {source.title}. Dripper: {recipe.dripper}. "
            f"Ratio: {recipe.ratio}, Dose: {recipe.dose_g}g, Water: {recipe.water_g}g, Temp: {recipe.water_temperature_c}°C, Grind: {recipe.grind_description}. "
            f"Coffee Origin: {recipe.country or 'Specialty'}, Process: {recipe.process or 'Washed'}, Roast: {recipe.roast_level or 'Medium'}. "
            f"Notes: {recipe.tasting_notes or 'Balanced fruit and sweetness'}. "
            f"Content: {raw_content[:300]}"
        )

        chunks = [summary_text]
        content_chunks = chunk_text(raw_content, chunk_size=300, overlap=50)
        for c in content_chunks[:3]:  # Limit to 3 content chunks for compactness
            if c not in chunks:
                chunks.append(c)

        # Generate embeddings
        embeddings = await self.embedding_provider.embed_documents(chunks)

        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            emb_record = RecipeEmbeddingModel(
                id=str(uuid.uuid4()),
                recipe_source_id=source.id,
                chunk_text=chunk,
                chunk_index=idx,
                embedding=emb,
                embedding_metadata={"chunk_type": "summary" if idx == 0 else "body"}
            )
            db.add(emb_record)

        await db.commit()
        await db.refresh(source)
        return source
