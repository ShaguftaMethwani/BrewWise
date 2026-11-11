import logging
from typing import List
import httpx

from brewwise.providers.search.base import SearchProvider, SearchResult

logger = logging.getLogger(__name__)


class TavilySearchProvider(SearchProvider):
    def __init__(self, api_key: str, timeout: float = 8.0):
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://api.tavily.com/search"

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        if not self.api_key:
            logger.warning("Tavily search API key not configured.")
            return []

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "include_domains": [],
            "exclude_domains": [],
            "max_results": max_results
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.base_url, json=payload)
                resp.raise_for_status()
                data = resp.json()

                raw_results = data.get("results", [])
                results = []
                for idx, item in enumerate(raw_results, 1):
                    results.append(
                        SearchResult(
                            url=item.get("url", ""),
                            title=item.get("title", ""),
                            snippet=item.get("content", ""),
                            position=idx,
                            source_name=item.get("url", "").split("//")[-1].split("/")[0]
                        )
                    )
                return results
        except Exception as e:
            logger.error(f"Tavily search API failed: {e}")
            raise
