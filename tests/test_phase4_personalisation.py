import pytest
from httpx import AsyncClient, ASGITransport
from brewwise.main import app
from brewwise.services.auth.jwt_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)
from brewwise.services.equipment.grinder_guide import (
    map_grind_setting,
    GRINDER_DATABASE,
    get_all_grinders
)
from brewwise.services.equipment.dripper_guide import (
    get_all_drippers,
    get_dripper_details
)
from brewwise.services.feedback.analyser import FeedbackAnalyser
from brewwise.schemas.brew import BrewLogCreate


def test_password_hashing_and_verification():
    pwd = "supersecretbarista123"
    pwd_hash, salt = hash_password(pwd)
    assert pwd_hash != pwd
    assert len(salt) == 32  # 16 bytes in hex is 32 chars
    assert verify_password(pwd, pwd_hash, salt) is True
    assert verify_password("wrongpassword", pwd_hash, salt) is False


def test_jwt_token_creation_and_decoding():
    token = create_access_token(user_id="user-123", email="barista@brewwise.com")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["email"] == "barista@brewwise.com"

    # Invalid token check
    assert decode_access_token("invalid.token.here") is None


def test_grinder_guide_and_click_mappings():
    grinders = get_all_grinders()
    assert len(grinders) >= 20  # 21 models supported
    
    # Comandante C40: Medium-Fine -> ~20-22 clicks
    comandante = map_grind_setting("Comandante C40", "Medium-Fine")
    assert comandante is not None
    assert "clicks" in comandante.lower()
    assert "Comandante C40" in comandante

    # Fellow Ode Gen 2: Medium
    fellow = map_grind_setting("Fellow Ode Gen 2", "Medium")
    assert fellow is not None
    assert "Fellow Ode" in fellow

    # Baratza Encore: Medium-Coarse
    encore = map_grind_setting("Baratza Encore", "Medium-Coarse")
    assert encore is not None
    assert "Baratza Encore" in encore

    # 1Zpresso J-Max typed in various ways
    jmax1 = map_grind_setting("1zpresso jmax", "Medium-Fine")
    assert jmax1 is not None
    assert "1Zpresso J-Max" in jmax1
    assert "3.0.0" in jmax1

    jmax2 = map_grind_setting("j-max", "Medium")
    assert jmax2 is not None
    assert "1Zpresso J-Max" in jmax2

    # Kingrinder K6 & ZP6
    k6 = map_grind_setting("k6", "Medium-Fine")
    assert k6 is not None
    assert "Kingrinder K6" in k6



def test_dripper_guide_details():
    drippers = get_all_drippers()
    assert len(drippers) >= 8
    hario = get_dripper_details("Hario V60")
    assert hario is not None
    assert hario["geometry"] == "Conical 60°"
    assert "filter" in hario


def test_feedback_analyser_under_extraction():
    brew_data = BrewLogCreate(
        actual_dose_g=15.0,
        actual_water_g=250.0,
        actual_grind_setting="26 clicks",
        actual_temp_c=90,
        actual_brew_time_seconds=140,
        sourness=5,  # Very sour
        bitterness=1,
        sweetness=1,
        body=2,
        overall_satisfaction=2,
        drawdown_speed="fast"
    )
    analysis = FeedbackAnalyser.analyse(brew_data)
    assert "Under-Extraction" in analysis.diagnosis
    assert "finer" in analysis.primary_adjustment.lower()
    assert "grind_adjustment" in analysis.suggested_parameters


def test_feedback_analyser_over_extraction():
    brew_data = BrewLogCreate(
        actual_dose_g=15.0,
        actual_water_g=250.0,
        actual_grind_setting="12 clicks",
        actual_temp_c=96,
        actual_brew_time_seconds=270,
        sourness=1,
        bitterness=5,  # Harsh bitterness
        sweetness=1,
        body=4,
        overall_satisfaction=2,
        drawdown_speed="slow"
    )
    analysis = FeedbackAnalyser.analyse(brew_data)
    # 270s or bitter >= 4 triggers Over-Extraction or Clogging
    assert "Extraction" in analysis.diagnosis or "Clogging" in analysis.diagnosis
    assert "coarser" in analysis.primary_adjustment.lower()


def test_feedback_analyser_channelling():
    brew_data = BrewLogCreate(
        actual_dose_g=15.0,
        actual_water_g=250.0,
        actual_grind_setting="20 clicks",
        actual_temp_c=93,
        actual_brew_time_seconds=190,
        sourness=4,  # Both sour AND bitter
        bitterness=4,
        sweetness=2,
        body=2,
        overall_satisfaction=2,
        drawdown_speed="normal"
    )
    analysis = FeedbackAnalyser.analyse(brew_data)
    assert "Channelling" in analysis.diagnosis
    assert "pour" in analysis.primary_adjustment.lower()


def test_feedback_analyser_balanced():
    brew_data = BrewLogCreate(
        actual_dose_g=15.0,
        actual_water_g=250.0,
        actual_grind_setting="22 clicks",
        actual_temp_c=93,
        actual_brew_time_seconds=185,
        sourness=3,
        bitterness=2,
        sweetness=4,
        body=3,
        overall_satisfaction=5,
        drawdown_speed="normal"
    )
    analysis = FeedbackAnalyser.analyse(brew_data)
    assert "Dialed-In" in analysis.diagnosis
    assert "Maintain exact" in analysis.primary_adjustment


@pytest.mark.asyncio
async def test_auth_and_equipment_and_brew_flow():
    import uuid
    unique_email = f"barista_{uuid.uuid4().hex[:8]}@example.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register a new user
        reg_payload = {
            "email": unique_email,
            "password": "coffeepassword123",
            "display_name": "Espresso Geek"
        }
        res_reg = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res_reg.status_code == 200
        auth_data = res_reg.json()
        token = auth_data["token"]
        assert token is not None
        assert auth_data["user"]["email"] == unique_email

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get current user profile
        res_me = await client.get("/api/v1/auth/me", headers=headers)
        assert res_me.status_code == 200
        assert res_me.json()["display_name"] == "Espresso Geek"

        # 3. Create an equipment profile
        profile_payload = {
            "name": "My Daily V60 Setup",
            "dripper": "Hario V60",
            "grinder": "Comandante C40",
            "filter_type": "Hario Tabbed White Filter",
            "default_dose_g": 15.0,
            "default_ratio": "1:16.67",
            "is_default": True
        }
        res_prof = await client.post("/api/v1/equipment/profiles", json=profile_payload, headers=headers)
        assert res_prof.status_code == 200
        profile_data = res_prof.json()
        assert profile_data["dripper"] == "Hario V60"
        profile_id = profile_data["id"]

        # List equipment profiles
        res_list = await client.get("/api/v1/equipment/profiles", headers=headers)
        assert res_list.status_code == 200
        assert len(res_list.json()) >= 1

        # 4. Log a brew with feedback
        brew_payload = {
            "dripper": "Hario V60",
            "grinder": "Comandante C40",
            "actual_dose_g": 15.0,
            "actual_water_g": 250.0,
            "actual_grind_setting": "25 clicks",
            "actual_temp_c": 92,
            "actual_brew_time_seconds": 150,
            "sourness": 4,
            "bitterness": 2,
            "sweetness": 2,
            "body": 2,
            "overall_satisfaction": 3,
            "drawdown_speed": "fast",
            "flavour_notes": "Bright citrus, slightly thin"
        }
        res_brew = await client.post("/api/v1/brews", json=brew_payload, headers=headers)
        assert res_brew.status_code == 200
        brew_data = res_brew.json()
        brew_id = brew_data["id"]
        assert brew_data["adjustments"] is not None
        assert "Under-Extraction" in brew_data["adjustments"]["diagnosis"]

        # 5. Get user brews
        res_brews = await client.get("/api/v1/brews", headers=headers)
        assert res_brews.status_code == 200
        brews_list = res_brews.json()
        assert len(brews_list) >= 1
        assert brews_list[0]["id"] == brew_id

        # 6. Update feedback on existing brew
        feedback_update = {
            "overall_satisfaction": 4,
            "flavour_notes": "Much better after cooling down",
            "sweetness": 4
        }
        res_update = await client.post(f"/api/v1/brews/{brew_id}/feedback", json=feedback_update, headers=headers)
        assert res_update.status_code == 200
        updated = res_update.json()
        assert updated["overall_satisfaction"] == 4
        assert updated["sweetness"] == 4
