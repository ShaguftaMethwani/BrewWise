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


@lru_cache()
def get_vision_provider() -> Optional[VisionProvider]:
    if settings.GOOGLE_API_KEY:
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


def get_recipe_generator() -> RecipeGenerator:
    llm_prov = get_llm_provider()
    cache_prov = get_cache_provider()
    return RecipeGenerator(
        llm_provider=llm_prov,
        cache_provider=cache_prov,
        model_name=settings.LLM_MODEL
    )
