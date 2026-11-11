import logging
from typing import List, Optional
import httpx

from brewwise.providers.search.base import SearchProvider, SearchResult

logger = logging.getLogger(__name__)


class GoogleSearchProvider(SearchProvider):
    def __init__(self, api_key: str, cx: str, timeout: float = 8.0):
        self.api_key = api_key
        self.cx = cx
        self.timeout = timeout
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        if not self.api_key or not self.cx:
            logger.warning("Google Custom Search not configured (missing api_key or cx).")
            return []

        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": min(max_results, 10),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(self.base_url, params=params)
                resp.raise_for_status()
                data = resp.json()

                items = data.get("items", [])
                results = []
                for idx, item in enumerate(items, 1):
                    results.append(
                        SearchResult(
                            url=item.get("link", ""),
                            title=item.get("title", ""),
                            snippet=item.get("snippet", ""),
                            position=idx,
                            source_name=item.get("displayLink")
                        )
                    )
                return results
        except Exception as e:
            logger.error(f"Google Custom Search API request failed: {e}")
            raise
