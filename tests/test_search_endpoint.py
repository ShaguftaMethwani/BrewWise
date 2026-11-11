import pytest
from httpx import AsyncClient, ASGITransport
from brewwise.main import app
from brewwise.db.session import init_db
from scripts.ingest_curated import seed_curated_knowledge_base


@pytest.mark.asyncio
async def test_search_and_grounded_recipe_flow():
    await init_db()
    await seed_curated_knowledge_base()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. First, create a coffee profile for Attikan Estate
        profile_data = {
            "brand": "Blue Tokai Coffee Roasters",
            "product_name": "Attikan Estate",
            "estate": "Attikan Estate",
            "country": "India",
            "region": "Biligirirangana Hills",
            "process": "Washed",
            "roast_level": "Medium-Dark"
        }

        # Query health endpoint
        health_resp = await client.get("/api/v1/health")
        assert health_resp.status_code == 200

        # We can simulate search with an existing profile or created profile
        from brewwise.db.session import AsyncSessionLocal
        from brewwise.models.coffee_profile import CoffeeProfileModel
        import uuid

        profile_id = str(uuid.uuid4())
        async with AsyncSessionLocal() as session:
            db_profile = CoffeeProfileModel(
                id=profile_id,
                brand="Blue Tokai Coffee Roasters",
                product_name="Attikan Estate",
                estate="Attikan Estate",
                country="India",
                region="Biligirirangana Hills",
                process="Washed",
                roast_level="Medium-Dark",
                varietal="SLN 9",
                confidence=0.92,
                raw_metadata={
                    "id": profile_id,
                    "brand": {"value": "Blue Tokai Coffee Roasters", "confidence": 0.95, "source": "bag_text"},
                    "product_name": {"value": "Attikan Estate", "confidence": 0.95, "source": "bag_text"},
                    "estate": {"value": "Attikan Estate", "confidence": 0.95, "source": "bag_text"},
                    "country": {"value": "India", "confidence": 0.95, "source": "bag_text"},
                    "process": {"value": "Washed", "confidence": 0.95, "source": "bag_text"},
                    "roast_level": {"value": "Medium-Dark", "confidence": 0.95, "source": "bag_text"},
                    "varietal": {"value": "SLN 9", "confidence": 0.90, "source": "bag_text"},
                    "tasting_notes": {"value": "Dark chocolate, fig", "confidence": 0.90, "source": "bag_text"},
                    "region": {"value": "Biligirirangana Hills", "confidence": 0.90, "source": "bag_text"},
                    "additional_info": [],
                    "extraction_model": "test",
                    "is_coffee_bag": True
                }
            )
            session.add(db_profile)
            await session.commit()

        # 2. Test POST /api/v1/recipes/search
        search_res = await client.post(
            "/api/v1/recipes/search",
            json={"coffee_profile_id": profile_id, "dripper": "Hario V60"}
        )
        assert search_res.status_code == 200
        search_data = search_res.json()

        assert search_data["match_outcome"] in ("A", "B")
        assert len(search_data["matched_recipes"]) > 0
        # The top match should be Blue Tokai Attikan Estate
        top_match = search_data["matched_recipes"][0]
        assert "Attikan" in top_match["title"]
        assert top_match["match_type"] in ("exact", "strong")

        # 3. Test POST /api/v1/recipes/generate
        gen_res = await client.post(
            "/api/v1/recipes/generate",
            json={
                "coffee_profile_id": profile_id,
                "dripper": "Hario V60",
                "dose_preference_g": 16.0
            }
        )
        assert gen_res.status_code == 200
        recipe_data = gen_res.json()

        assert recipe_data["dose_g"] == 16.0
        assert recipe_data["source_type"] in ("exact_match", "adapted_from_related")
        assert len(recipe_data["source_recipes"]) > 0
        assert any("Attikan" in s["source_name"] or "bluetokaicoffee" in (s.get("url") or "") for s in recipe_data["source_recipes"])
        # Check recipe arithmetic
        total_pour = sum(p["water_g"] for p in recipe_data["pour_schedule"])
        assert abs(total_pour - recipe_data["water_g"]) <= 1.0
