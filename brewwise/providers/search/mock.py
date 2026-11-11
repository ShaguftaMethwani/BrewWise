import logging
from typing import List, Optional
from brewwise.providers.search.base import SearchProvider, SearchResult

logger = logging.getLogger(__name__)


class MockSearchProvider(SearchProvider):
    def __init__(self, should_fail: bool = False, custom_results: Optional[List[SearchResult]] = None):
        self.should_fail = should_fail
        self.custom_results = custom_results

    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        if self.should_fail:
            raise ConnectionError("Simulated search API network failure")

        if self.custom_results is not None:
            return self.custom_results[:max_results]

        lower = query.lower()
        results: List[SearchResult] = []

        if "attikan" in lower or "blue tokai" in lower:
            results.append(
                SearchResult(
                    url="https://bluetokaicoffee.com/blogs/brewing-guides/v60-attikan-estate",
                    title="How to Brew Attikan Estate on Hario V60 — Blue Tokai",
                    snippet="Brewing guide for Attikan Estate washed coffee using Hario V60 pour-over dripper.",
                    position=1,
                    source_name="bluetokaicoffee.com"
                )
            )
        elif "kerehaklu" in lower or "subko" in lower:
            results.append(
                SearchResult(
                    url="https://subko.coffee/blogs/recipes/kerehaklu-v60-guide",
                    title="Subko Kerehaklu Estate Honey Process V60 Recipe",
                    snippet="Official brew bar recipe for Kerehaklu Honey Lot: 15g coffee, 250g water at 94°C.",
                    position=1,
                    source_name="subko.coffee"
                )
            )
        elif "ethiopia" in lower or "yirgacheffe" in lower:
            results.append(
                SearchResult(
                    url="https://squaremilecoffee.com/brew-guides/v60-worka-sakaro",
                    title="Square Mile Coffee Roasters — Worka Sakaro Ethiopia V60",
                    snippet="Delicate floral peach notes: recommended pour-over parameters for washed Ethiopian coffees.",
                    position=1,
                    source_name="squaremilecoffee.com"
                )
            )
        elif "colombia" in lower or "paraiso" in lower:
            results.append(
                SearchResult(
                    url="https://onyxcoffeelab.com/blogs/brewing-guides/el-paraiso-anaerobic-v60",
                    title="Onyx Coffee Lab — El Paraiso Colombia Pour-Over",
                    snippet="Brewing guide for anaerobic fermented Colombia Castillo: lower brew temp to preserve tropical fruit aromatics.",
                    position=1,
                    source_name="onyxcoffeelab.com"
                )
            )

        # Generic pour-over fallback result if query doesn't match specific roaster
        if not results:
            results.append(
                SearchResult(
                    url="https://kurasu.kyoto/blogs/brew-guide/v60-pour-over-standard",
                    title="Kurasu Kyoto Standard Pour-Over V60 Guide",
                    snippet="General precision pour-over method for specialty coffee beans: 1:16 ratio at 92°C.",
                    position=1,
                    source_name="kurasu.kyoto"
                )
            )

        return results[:max_results]
