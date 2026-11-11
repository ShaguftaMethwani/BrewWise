import hashlib
import logging
import math
from typing import List, Optional
from brewwise.providers.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)


def generate_deterministic_embedding(text: str, dim: int = 768) -> List[float]:
    """Generates a stable normalized 768-dim pseudo-embedding vector from text.
    Used as an offline/testing fallback when Gemini API key is unavailable."""
    words = text.lower().split()
    vec = [0.0] * dim
    if not words:
        return vec

    for i, word in enumerate(words):
        h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        # Distribute hash entropy across positions
        idx = h % dim
        weight = 1.0 / (1.0 + math.log(i + 1))
        vec[idx] += weight
        vec[(idx + 384) % dim] += weight * 0.5

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [round(x / norm, 6) for x in vec]
    return vec


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-004",
        dimension: int = 768
    ):
        self.api_key = api_key
        self.model = model
        self.dimension = dimension
        self.client = None

        if api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
            except Exception as e:
                logger.warning(f"Could not initialize google-genai Client for embeddings: {e}")

    async def embed_query(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dimension

        if self.client:
            try:
                # Synchronous client call inside async wrapper
                import asyncio
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.models.embed_content(
                        model=self.model,
                        contents=text,
                    )
                )
                if response and hasattr(response, "embedding") and response.embedding:
                    values = response.embedding.values
                    return list(values)[:self.dimension]
                elif response and hasattr(response, "embeddings") and response.embeddings:
                    return list(response.embeddings[0].values)[:self.dimension]
            except Exception as e:
                logger.warning(f"Gemini API embed_content failed, falling back to deterministic: {e}")

        return generate_deterministic_embedding(text, dim=self.dimension)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self.client:
            try:
                import asyncio
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.models.embed_content(
                        model=self.model,
                        contents=texts,
                    )
                )
                if response and hasattr(response, "embeddings") and response.embeddings:
                    return [list(emb.values)[:self.dimension] for emb in response.embeddings]
            except Exception as e:
                logger.warning(f"Gemini API embed_documents failed, falling back to deterministic: {e}")

        return [generate_deterministic_embedding(t, dim=self.dimension) for t in texts]
