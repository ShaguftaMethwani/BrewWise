from typing import List, Optional
from brewwise.schemas.coffee_profile import CoffeeProfileDraft


class QueryBuilder:
    @staticmethod
    def build_queries(
        profile: CoffeeProfileDraft,
        dripper: Optional[str] = "Hario V60"
    ) -> List[str]:
        """Constructs multiple search query variants to maximize hybrid retrieval recall and precision."""
        queries = []

        brand = profile.brand.value if profile.brand and profile.brand.value else ""
        estate = profile.estate.value if profile.estate and profile.estate.value else ""
        product_name = profile.product_name.value if profile.product_name and profile.product_name.value else ""
        country = profile.country.value if profile.country and profile.country.value else ""
        region = profile.region.value if profile.region and profile.region.value else ""
        process = profile.process.value if profile.process and profile.process.value else ""
        roast = profile.roast_level.value if profile.roast_level and profile.roast_level.value else ""
        varietal = profile.varietal.value if profile.varietal and profile.varietal.value else ""

        # 1. Exact query: brand + estate + product_name
        exact_parts = [p for p in [brand, estate, product_name] if p]
        if exact_parts:
            queries.append(" ".join(exact_parts))

        # 2. Producer / Origin query: estate + country + process
        producer_parts = [p for p in [estate, region or country, process] if p]
        if producer_parts and " ".join(producer_parts) not in queries:
            queries.append(" ".join(producer_parts))

        # 3. Characteristic query: process + roast + varietal + country + pour-over
        char_parts = [p for p in [process, roast, varietal, country, "pour-over"] if p]
        if char_parts:
            queries.append(" ".join(char_parts))

        # 4. Equipment query if dripper specified
        if dripper:
            queries.append(f"{dripper} pour-over recipe")

        # Fallback if profile is completely sparse
        if not queries:
            queries.append("Specialty pour-over recipe")

        return queries
