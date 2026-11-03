import time
import json
import logging
from typing import Optional, Dict, Tuple
from brewwise.providers.cache.base import CacheProvider

logger = logging.getLogger(__name__)


class HybridCacheProvider(CacheProvider):
    """
    Attempts to use Redis if available; gracefully falls back to an in-memory dictionary.
    """
    def __init__(self, redis_url: Optional[str] = None):
        self._memory_cache: Dict[str, Tuple[str, Optional[float]]] = {}
        self._redis_client = None
        self._redis_failed = False

        if redis_url:
            try:
                import redis.asyncio as aioredis
                self._redis_client = aioredis.from_url(redis_url, decode_responses=True)
            except Exception as e:
                logger.warning(f"Could not initialize Redis client ({e}). Falling back to in-memory cache.")
                self._redis_failed = True

    async def get(self, key: str) -> Optional[str]:
        if self._redis_client and not self._redis_failed:
            try:
                return await self._redis_client.get(key)
            except Exception as e:
                logger.debug(f"Redis get failed: {e}. Falling back to memory cache.")
                self._redis_failed = True

        # In-memory lookup
        if key in self._memory_cache:
            val, expiry = self._memory_cache[key]
            if expiry is None or expiry > time.time():
                return val
            del self._memory_cache[key]
        return None

    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        if self._redis_client and not self._redis_failed:
            try:
                if ttl_seconds:
                    await self._redis_client.setex(key, ttl_seconds, value)
                else:
                    await self._redis_client.set(key, value)
                return True
            except Exception as e:
                logger.debug(f"Redis set failed: {e}. Falling back to memory cache.")
                self._redis_failed = True

        expiry = (time.time() + ttl_seconds) if ttl_seconds else None
        self._memory_cache[key] = (value, expiry)
        return True

    async def delete(self, key: str) -> bool:
        if self._redis_client and not self._redis_failed:
            try:
                await self._redis_client.delete(key)
                return True
            except Exception:
                self._redis_failed = True

        if key in self._memory_cache:
            del self._memory_cache[key]
            return True
        return False
