import hashlib
import os
import json
import logging
from typing import Optional
from brewwise.services.vision.base import VisionProvider
from brewwise.providers.storage.base import StorageProvider
from brewwise.providers.cache.base import CacheProvider
from brewwise.schemas.scan import CoffeeProfileDraftCompact
from brewwise.schemas.coffee_profile import CoffeeProfileDraft
from brewwise.services.identity.normaliser import normalise_profile

logger = logging.getLogger(__name__)


class CoffeeBagExtractor:
    def __init__(
        self,
        vision_provider: VisionProvider,
        storage_provider: StorageProvider,
        cache_provider: Optional[CacheProvider] = None,
        model_name: str = "gemini-2.5-flash"
    ):
        self.vision_provider = vision_provider
        self.storage_provider = storage_provider
        self.cache_provider = cache_provider
        self.model_name = model_name

    async def extract(
        self,
        image_bytes: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> CoffeeProfileDraft:
        # 1. SHA-256 hash
        sha256 = hashlib.sha256(image_bytes).hexdigest()
        cache_key = f"scan:{sha256}"

        # 2. Check cache
        if self.cache_provider:
            cached_json = await self.cache_provider.get(cache_key)
            if cached_json:
                try:
                    logger.info(f"Cache hit for coffee bag image hash {sha256}")
                    return CoffeeProfileDraft.model_validate_json(cached_json)
                except Exception as e:
                    logger.warning(f"Failed to deserialize cached profile: {e}")

        # 3. Vision extraction (before storing anything, so rejected uploads are not retained)
        if not self.vision_provider:
            raise ValueError(
                "Image extraction is not configured. Set GOOGLE_API_KEY on the server to scan coffee bags, "
                "or enter the coffee details manually."
            )
        compact = await self.vision_provider.extract_coffee_profile(image_bytes, content_type)

        # 4. Store image only for genuine coffee bags
        storage_id = f"{sha256}_{os.path.basename(filename)}"
        image_url = None
        if compact.is_coffee_bag:
            await self.storage_provider.upload(image_bytes, storage_id, content_type)
            image_url = await self.storage_provider.get_url(storage_id)

        # 5. Inflate compact to full schema
        draft = CoffeeProfileDraft.from_compact(
            compact=compact,
            image_id=storage_id,
            image_url=image_url,
            model=self.model_name
        )

        # 6. Normalise canonical fields
        draft = normalise_profile(draft)

        # 7. Cache result (30 days TTL = 2592000s)
        if self.cache_provider and draft.is_coffee_bag:
            try:
                await self.cache_provider.set(cache_key, draft.model_dump_json(), ttl_seconds=2592000)
            except Exception as e:
                logger.warning(f"Failed to cache scan result: {e}")

        return draft
