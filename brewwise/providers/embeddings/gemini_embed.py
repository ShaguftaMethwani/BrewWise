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
        model: str = "gemini-embedding-001",
        dimension: int = 768
    ):
        self.api_key = api_key
        self.model = model
        self.dimension = dimension
        self.client = None

        if api_key:
            try:
                from google import genai
                # Uses standard v1 API by default for embeddings
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.warning(f"Could not initialize google-genai Client for embeddings: {e}")

    def _normalize_vec(self, values: List[float]) -> List[float]:
        """Ensures vector is exactly self.dimension and L2 normalized."""
        if len(values) > self.dimension:
            values = values[:self.dimension]
        elif len(values) < self.dimension:
            values = values + [0.0] * (self.dimension - len(values))
        norm = math.sqrt(sum(x * x for x in values))
        if norm > 0:
            values = [round(x / norm, 6) for x in values]
        return values

    def _embed_sync(self, contents):
        """Attempts embedding with self.model, falling back to alternative active models if 404."""
        models = [self.model]
        if self.model != "gemini-embedding-001":
            models.append("gemini-embedding-001")
        if "text-embedding-004" not in models:
            models.append("text-embedding-004")

        last_err = None
        for m in models:
            try:
                try:
                    res = self.client.models.embed_content(
                        model=m,
                        contents=contents,
                        config={"output_dimensionality": self.dimension}
                    )
                except Exception:
                    res = self.client.models.embed_content(
                        model=m,
                        contents=contents,
                    )
                if m != self.model:
                    logger.info(f"Gemini embedding model automatically switched from {self.model} to {m}")
                    self.model = m
                return res
            except Exception as e:
                last_err = e
                err_msg = str(e)
                if "404" in err_msg or "NOT_FOUND" in err_msg or "not found" in err_msg:
                    continue
                raise e
        raise last_err

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
                    lambda: self._embed_sync(text)
                )
                if response and hasattr(response, "embedding") and response.embedding:
                    return self._normalize_vec(list(response.embedding.values))
                elif response and hasattr(response, "embeddings") and response.embeddings:
                    return self._normalize_vec(list(response.embeddings[0].values))
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
                    lambda: self._embed_sync(texts)
                )
                if response and hasattr(response, "embeddings") and response.embeddings:
                    return [self._normalize_vec(list(emb.values)) for emb in response.embeddings]
            except Exception as e:
                logger.warning(f"Gemini API embed_documents failed, falling back to deterministic: {e}")

        return [generate_deterministic_embedding(t, dim=self.dimension) for t in texts]
