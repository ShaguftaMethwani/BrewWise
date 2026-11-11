import math
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from brewwise.models.recipe_source import RecipeSourceModel, RecipeEmbeddingModel
from brewwise.providers.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class HybridRetriever:
    def __init__(self, embedding_provider: EmbeddingProvider, rrf_k: int = 60):
        self.embedding_provider = embedding_provider
        self.rrf_k = rrf_k

    async def search(
        self,
        queries: List[str],
        db: AsyncSession,
        top_k: int = 20
    ) -> List[Tuple[RecipeSourceModel, float]]:
        """Executes full-text/keyword and vector search across queries, merging with RRF."""
        if not queries:
            return []

        # Load all sources with their embeddings
        stmt = select(RecipeSourceModel).options(selectinload(RecipeSourceModel.embeddings))
        res = await db.execute(stmt)
        all_sources = res.scalars().all()
        if not all_sources:
            return []

        # Embed all query strings
        query_embeddings = await self.embedding_provider.embed_documents(queries)

        # 1. Vector Search scoring
        # For each source, find max cosine similarity across all query vectors and all source chunks
        vector_scores: Dict[str, float] = {}
        for source in all_sources:
            max_sim = 0.0
            for emb_record in source.embeddings:
                emb_vec = emb_record.embedding
                if not emb_vec:
                    continue
                for q_vec in query_embeddings:
                    sim = cosine_similarity(q_vec, emb_vec)
                    if sim > max_sim:
                        max_sim = sim
            vector_scores[source.id] = max_sim

        # 2. Text / Keyword Search scoring
        # Token overlap and matching against title, metadata, and raw_content
        keyword_scores: Dict[str, float] = {}
        for source in all_sources:
            searchable_text = f"{source.title or ''} {source.raw_content or ''}"
            if source.coffee_metadata:
                searchable_text += " " + " ".join(str(v) for v in source.coffee_metadata.values() if v)
            lower_text = searchable_text.lower()

            match_score = 0.0
            for query in queries:
                q_tokens = [t.lower() for t in query.split() if len(t) > 2]
                if not q_tokens:
                    continue
                hits = sum(1 for t in q_tokens if t in lower_text)
                ratio = hits / len(q_tokens)
                if query.lower() in lower_text:
                    ratio += 1.0  # Exact phrase bonus
                match_score = max(match_score, ratio)

            keyword_scores[source.id] = match_score

        # Rank sources by vector score
        sorted_by_vector = sorted(all_sources, key=lambda s: vector_scores.get(s.id, 0.0), reverse=True)
        # Rank sources by keyword score
        sorted_by_keyword = sorted(all_sources, key=lambda s: keyword_scores.get(s.id, 0.0), reverse=True)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {s.id: 0.0 for s in all_sources}
        for rank, source in enumerate(sorted_by_vector):
            rrf_scores[source.id] += 1.0 / (self.rrf_k + rank + 1)
        for rank, source in enumerate(sorted_by_keyword):
            rrf_scores[source.id] += 1.0 / (self.rrf_k + rank + 1)

        # Sort all sources by combined RRF score
        sorted_sources = sorted(all_sources, key=lambda s: rrf_scores[s.id], reverse=True)

        return [(s, round(rrf_scores[s.id], 5)) for s in sorted_sources[:top_k]]
