import pytest
from brewwise.services.identity.normaliser import (
    normalise_roaster_name,
    normalise_process_method,
    normalise_roast_level,
    clean_text,
    normalise_profile
)
from brewwise.schemas.coffee_profile import CoffeeProfileDraft, ExtractedField


def test_clean_text():
    assert clean_text("  Blue   Tokai  ") == "Blue Tokai"
    assert clean_text("Café  de   Colombia") == "Café de Colombia"
    assert clean_text("") is None


def test_normalise_roaster_name():
    assert normalise_roaster_name("Blue Tokai Coffee Roasters") == "Blue Tokai"
    assert normalise_roaster_name("Subko Specialty Coffee Co.") == "Subko"
    assert normalise_roaster_name("Kurasu Kyoto Roasters") == "Kurasu Kyoto"
    assert normalise_roaster_name("Tim Wendelboe Coffee") == "Tim Wendelboe"
    assert normalise_roaster_name("James Gourmet Coffee Co") == "James Gourmet"


def test_normalise_process_method():
    test_cases = [
        ("Natural Process", "natural"),
        ("natural", "natural"),
        ("Fully Washed", "washed"),
        ("washed process", "washed"),
        ("Washed", "washed"),
        ("Honey Process", "honey"),
        ("Yellow Honey", "yellow_honey"),
        ("Anaerobic Natural", "anaerobic_natural"),
        ("Anaerobic Nat", "anaerobic_natural"),
        ("Anaerobic Washed", "anaerobic_washed"),
        ("Carbonic Maceration", "carbonic_maceration"),
        ("Thermal Shock", "thermal_shock"),
    ]
    for raw, expected in test_cases:
        assert normalise_process_method(raw) == expected


def test_normalise_roast_level():
    test_cases = [
        ("Light Roast", "light"),
        ("light", "light"),
        ("Filter Roast", "light"),
        ("Medium-Light", "medium_light"),
        ("Medium Light", "medium_light"),
        ("Medium Roast", "medium"),
        ("Medium", "medium"),
        ("City", "medium"),
        ("Medium-Dark", "medium_dark"),
        ("Full City", "medium_dark"),
        ("Dark Roast", "dark"),
        ("Omni Roast", "omni"),
    ]
    for raw, expected in test_cases:
        assert normalise_roast_level(raw) == expected


def test_normalise_profile():
    draft = CoffeeProfileDraft(
        brand=ExtractedField(value="Blue Tokai Coffee Roasters", confidence=0.95),
        product_name=ExtractedField(value="Attikan Estate  ", confidence=0.90),
        estate=ExtractedField(value="Attikan Estate", confidence=0.90),
        country=ExtractedField(value="India", confidence=0.99),
        region=ExtractedField(value="Biligirirangana Hills", confidence=0.85),
        varietal=ExtractedField(value="SLN 795", confidence=0.90),
        process=ExtractedField(value="Fully Washed", confidence=0.92),
        roast_level=ExtractedField(value="Medium-Light", confidence=0.88),
        roast_date=ExtractedField(value="2026-10-15", confidence=0.95),
        tasting_notes=ExtractedField(value="Dark Chocolate, Fig, Roasted Almond", confidence=0.85),
        altitude=ExtractedField(value="1600m", confidence=0.80),
    )

    normalised = normalise_profile(draft)
    assert normalised.brand.value == "Blue Tokai"
    assert normalised.process.value == "washed"
    assert normalised.roast_level.value == "medium_light"
