import uuid
from typing import List, Tuple
from brewwise.models.recipe_source import RecipeSourceModel
from brewwise.services.discovery.recipe_extractor import DiscoveredRecipe


class ResultMerger:
    @staticmethod
    def merge(
        live_recipes: List[DiscoveredRecipe],
        local_candidates: List[Tuple[RecipeSourceModel, float]]
    ) -> List[Tuple[RecipeSourceModel, float]]:
        """Merges freshly discovered live web recipes into local knowledge base candidates."""
        existing_urls = {c[0].url for c in local_candidates if c[0].url}
        merged = list(local_candidates)

        for live in live_recipes:
            if live.url in existing_urls:
                continue

            # Convert DiscoveredRecipe to RecipeSourceModel format
            transient_source = RecipeSourceModel(
                id=str(uuid.uuid4()),
                url=live.url,
                title=live.title,
                author=live.author or "Online Discovery",
                site_name=live.site_name,
                raw_content=live.instructions or f"Discovered pour-over recipe: {live.title}",
                content_hash="live-" + uuid.uuid4().hex[:12],
                extraction_method="live_search",
                is_accessible=True,
                coffee_metadata=live.coffee_metadata or {},
                extracted_recipe={
                    "dripper": live.dripper,
                    "dose_g": live.dose_g,
                    "water_g": live.water_g,
                    "ratio": live.ratio,
                    "water_temperature_c": live.water_temperature_c,
                    "grind_description": live.grind_description,
                }
            )
            # Give live discovered results an active initial retrieval score (0.88)
            merged.append((transient_source, 0.88))
            existing_urls.add(live.url)

        return merged
