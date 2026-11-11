from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    position: int = 1
    source_name: Optional[str] = None


class SearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Executes web search query and returns top candidate URLs with snippets.
        NOTE: Snippets are used ONLY for ranking/filtering URLs, never for recipe extraction."""
        pass
