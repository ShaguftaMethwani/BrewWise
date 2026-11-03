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
