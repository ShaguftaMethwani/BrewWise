import pytest
from httpx import AsyncClient, ASGITransport
from brewwise.main import app
from brewwise.db.session import init_db
from brewwise.db.seed import seed_equipment


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    await seed_equipment()


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "BrewWise"


@pytest.mark.asyncio
async def test_equipment_catalogue():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        drippers_res = await ac.get("/api/v1/equipment/drippers")
        grinders_res = await ac.get("/api/v1/equipment/grinders")

    assert drippers_res.status_code == 200
    drippers = drippers_res.json()
    assert len(drippers) >= 5
    assert any(d["brand"] == "Hario" for d in drippers)

    assert grinders_res.status_code == 200
    grinders = grinders_res.json()
    assert len(grinders) >= 5
    assert any(g["brand"] == "Comandante" for g in grinders)


@pytest.mark.asyncio
async def test_update_coffee_profile():
    import uuid
    from brewwise.models.coffee_profile import CoffeeProfileModel
    from brewwise.db.session import AsyncSessionLocal

    profile_id = f"test-prof-{uuid.uuid4()}"
    async with AsyncSessionLocal() as session:
        prof = CoffeeProfileModel(
            id=profile_id,
            brand="Original Brand",
            product_name="Original Product",
            confidence=0.8,
            raw_metadata={
                "brand": {"value": "Original Brand", "confidence": 0.8, "source": "bag_text"},
                "product_name": {"value": "Original Product", "confidence": 0.8, "source": "bag_text"},
            }
        )
        session.add(prof)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        update_res = await ac.put(
            f"/api/v1/profiles/{profile_id}",
            json={
                "brand": "Overridden Brand",
                "process": "Washed"
            }
        )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["brand"]["value"] == "Overridden Brand"
    assert data["brand"]["source"] == "user_override"
    assert data["brand"]["confidence"] == 1.0
    assert data["process"]["value"] == "Washed"
    assert data["process"]["source"] == "user_override"

