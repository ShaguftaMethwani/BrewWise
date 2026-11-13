import logging
from functools import lru_cache
from typing import Optional

from brewwise.config import settings, Settings
from brewwise.providers.storage.base import StorageProvider
from brewwise.providers.storage.local import LocalStorageProvider
from brewwise.providers.cache.base import CacheProvider
from brewwise.providers.cache.provider import HybridCacheProvider
from brewwise.providers.llm.base import LLMProvider
from brewwise.providers.llm.gemini import GeminiLLMProvider
from brewwise.services.vision.base import VisionProvider
from brewwise.services.vision.gemini_vision import GeminiVisionProvider
from brewwise.services.vision.extractor import CoffeeBagExtractor
from brewwise.services.synthesis.recipe_generator import RecipeGenerator


logger = logging.getLogger(__name__)


@lru_cache()
def get_settings() -> Settings:
    return settings


@lru_cache()
def get_storage_provider() -> StorageProvider:
    return LocalStorageProvider(base_dir=settings.LOCAL_STORAGE_DIR)


@lru_cache()
def get_cache_provider() -> CacheProvider:
    return HybridCacheProvider(redis_url=settings.REDIS_URL)


@lru_cache()
def get_llm_provider() -> Optional[LLMProvider]:
    if settings.GOOGLE_API_KEY:
        return GeminiLLMProvider(api_key=settings.GOOGLE_API_KEY, default_model=settings.LLM_MODEL)
    return None


from brewwise.services.vision.mock_vision import MockVisionProvider


@lru_cache()
def get_vision_provider() -> Optional[VisionProvider]:
    # The mock returns a fixed sample profile, so it is only used when explicitly requested
    # (VISION_PROVIDER=mock) and never as a silent stand-in for real extraction.
    if settings.VISION_PROVIDER.lower() == "mock":
        return MockVisionProvider()
    if settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY.strip() != "":
        return GeminiVisionProvider(api_key=settings.GOOGLE_API_KEY, model=settings.LLM_MODEL)
    return None


def get_coffee_extractor() -> CoffeeBagExtractor:
    vision_prov = get_vision_provider()
    storage_prov = get_storage_provider()
    cache_prov = get_cache_provider()
    return CoffeeBagExtractor(
        vision_provider=vision_prov,
        storage_provider=storage_prov,
        cache_provider=cache_prov,
        model_name=settings.LLM_MODEL
    )


from brewwise.providers.embeddings.base import EmbeddingProvider
from brewwise.providers.embeddings.gemini_embed import GeminiEmbeddingProvider
from brewwise.services.retrieval.hybrid_retriever import HybridRetriever


def get_recipe_generator() -> RecipeGenerator:
    llm_prov = get_llm_provider()
    cache_prov = get_cache_provider()
    return RecipeGenerator(
        llm_provider=llm_prov,
        cache_provider=cache_prov,
        model_name=settings.LLM_MODEL
    )


@lru_cache()
def get_embedding_provider() -> EmbeddingProvider:
    return GeminiEmbeddingProvider(
        api_key=settings.GOOGLE_API_KEY,
        model=settings.EMBEDDING_MODEL
    )


def get_hybrid_retriever() -> HybridRetriever:
    return HybridRetriever(embedding_provider=get_embedding_provider())


from brewwise.providers.search.base import SearchProvider
from brewwise.providers.search.google_search import GoogleSearchProvider
from brewwise.providers.search.tavily import TavilySearchProvider
from brewwise.providers.search.mock import MockSearchProvider
from brewwise.services.discovery.orchestrator import DiscoveryOrchestrator


@lru_cache()
def get_search_provider() -> Optional[SearchProvider]:
    provider = settings.SEARCH_PROVIDER.lower()
    if provider == "google" and settings.SEARCH_API_KEY and settings.GOOGLE_SEARCH_CX:
        return GoogleSearchProvider(api_key=settings.SEARCH_API_KEY, cx=settings.GOOGLE_SEARCH_CX)
    elif provider == "tavily" and (settings.TAVILY_API_KEY or settings.SEARCH_API_KEY):
        return TavilySearchProvider(api_key=settings.TAVILY_API_KEY or settings.SEARCH_API_KEY)
    if provider not in ("none", ""):
        # "mock" returns canned URLs and is a test double only; without a real provider and key
        # live discovery reports itself as not configured instead of pretending to search.
        logger.warning(
            "SEARCH_PROVIDER=%s is not usable (unknown provider or missing API key); live web discovery is disabled.",
            provider,
        )
    return None


def get_discovery_orchestrator() -> DiscoveryOrchestrator:
    return DiscoveryOrchestrator(
        search_provider=get_search_provider(),
        cache_provider=get_cache_provider(),
        embedding_provider=get_embedding_provider(),
        llm_provider=get_llm_provider()
    )


