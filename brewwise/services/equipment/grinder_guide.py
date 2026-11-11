import re
from typing import Dict, Optional, Any

GRINDER_CATALOGUE: Dict[str, Dict[str, Any]] = {
    "Comandante C40": {
        "brand": "Comandante",
        "model": "C40 MK3/MK4",
        "burr_type": "39mm Nitro Blade Conical",
        "pourover_range": "18 - 28 clicks",
        "aliases": ["c40", "comandante", "c40 mk3", "c40 mk4", "comandante c40"],
        "mappings": {
            "fine": "16 clicks",
            "medium-fine": "22 clicks",
            "medium": "25 clicks",
            "medium-coarse": "28 clicks",
            "coarse": "32 clicks",
        }
    },
    "1Zpresso JX-Pro": {
        "brand": "1Zpresso",
        "model": "JX-Pro",
        "burr_type": "48mm Conical Stainless Steel",
        "pourover_range": "2.8.0 - 3.8.0",
        "aliases": ["jxpro", "jx-pro", "jx pro", "1zpresso jxpro", "1zpresso jx-pro"],
        "mappings": {
            "fine": "2.6.0",
            "medium-fine": "3.2.0",
            "medium": "3.5.0",
            "medium-coarse": "3.8.0",
            "coarse": "4.2.0",
        }
    },
    "1Zpresso J-Max": {
        "brand": "1Zpresso",
        "model": "J-Max / J-Ultra",
        "burr_type": "48mm Titanium-Coated Conical",
        "pourover_range": "2.8.0 - 3.6.0 (approx 250 - 320 clicks)",
        "aliases": ["jmax", "j-max", "jultra", "j-ultra", "1zpresso jmax", "1zpresso j-max"],
        "mappings": {
            "fine": "2.6.0 (~234 clicks)",
            "medium-fine": "3.0.0 (~270 clicks)",
            "medium": "3.2.0 (~288 clicks)",
            "medium-coarse": "3.5.0 (~315 clicks)",
            "coarse": "3.8.0 (~342 clicks)",
        }
    },
    "1Zpresso ZP6 Special": {
        "brand": "1Zpresso",
        "model": "ZP6 Special",
        "burr_type": "48mm ZP6 Hexagonal Burr",
        "pourover_range": "3.5 - 5.5",
        "aliases": ["zp6", "zp-6", "zp6 special", "1zpresso zp6"],
        "mappings": {
            "fine": "3.0",
            "medium-fine": "4.0",
            "medium": "4.5",
            "medium-coarse": "5.0",
            "coarse": "5.5",
        }
    },
    "1Zpresso X-Pro": {
        "brand": "1Zpresso",
        "model": "X-Pro / X-Ultra",
        "burr_type": "40mm Conical",
        "pourover_range": "2.0.0 - 2.5.0",
        "aliases": ["xpro", "x-pro", "xultra", "x-ultra", "1zpresso xpro"],
        "mappings": {
            "fine": "1.8.0",
            "medium-fine": "2.1.0",
            "medium": "2.2.0",
            "medium-coarse": "2.4.0",
            "coarse": "2.6.0",
        }
    },
    "Kingrinder K6": {
        "brand": "Kingrinder",
        "model": "K6",
        "burr_type": "48mm Heptagonal Conical",
        "pourover_range": "80 - 105 clicks",
        "aliases": ["k6", "kingrinder k6", "kin grinder k6"],
        "mappings": {
            "fine": "70 clicks",
            "medium-fine": "85 clicks",
            "medium": "95 clicks",
            "medium-coarse": "105 clicks",
            "coarse": "115 clicks",
        }
    },
    "Kingrinder K4": {
        "brand": "Kingrinder",
        "model": "K4",
        "burr_type": "48mm Titanium Conical",
        "pourover_range": "110 - 145 clicks",
        "aliases": ["k4", "kingrinder k4"],
        "mappings": {
            "fine": "100 clicks",
            "medium-fine": "120 clicks",
            "medium": "130 clicks",
            "medium-coarse": "145 clicks",
            "coarse": "160 clicks",
        }
    },
    "1Zpresso K-Ultra": {
        "brand": "1Zpresso",
        "model": "K-Ultra / K-Max",
        "burr_type": "48mm K-Burr Stainless Steel",
        "pourover_range": "6.0 - 8.0",
        "mappings": {
            "fine": "5.5",
            "medium-fine": "7.0",
            "medium": "7.5",
            "medium-coarse": "8.0",
            "coarse": "8.5",
        }
    },
    "1Zpresso Q2": {
        "brand": "1Zpresso",
        "model": "Q2 Seven Core",
        "burr_type": "38mm Conical",
        "pourover_range": "18 - 25 clicks",
        "mappings": {
            "fine": "16 clicks",
            "medium-fine": "21 clicks",
            "medium": "23 clicks",
            "medium-coarse": "26 clicks",
            "coarse": "29 clicks",
        }
    },
    "Timemore C2": {
        "brand": "Timemore",
        "model": "Chestnut C2 / C3",
        "burr_type": "38mm Conical Steel",
        "pourover_range": "13 - 18 clicks",
        "mappings": {
            "fine": "11 clicks",
            "medium-fine": "14 clicks",
            "medium": "16 clicks",
            "medium-coarse": "18 clicks",
            "coarse": "21 clicks",
        }
    },
    "Timemore Slim Plus": {
        "brand": "Timemore",
        "model": "Slim Plus",
        "burr_type": "E&B Conical Steel",
        "pourover_range": "14 - 20 clicks",
        "mappings": {
            "fine": "12 clicks",
            "medium-fine": "16 clicks",
            "medium": "18 clicks",
            "medium-coarse": "20 clicks",
            "coarse": "23 clicks",
        }
    },
    "Baratza Encore": {
        "brand": "Baratza",
        "model": "Encore",
        "burr_type": "40mm Conical M2/M3",
        "pourover_range": "10 - 18",
        "mappings": {
            "fine": "8",
            "medium-fine": "12",
            "medium": "14",
            "medium-coarse": "16",
            "coarse": "20",
        }
    },
    "Baratza Virtuoso+": {
        "brand": "Baratza",
        "model": "Virtuoso+",
        "burr_type": "40mm Conical M2",
        "pourover_range": "12 - 20",
        "mappings": {
            "fine": "10",
            "medium-fine": "14",
            "medium": "16",
            "medium-coarse": "18",
            "coarse": "22",
        }
    },
    "Baratza Sette 30": {
        "brand": "Baratza",
        "model": "Sette 30 / 270",
        "burr_type": "40mm Conical AP",
        "pourover_range": "20 - 30",
        "mappings": {
            "fine": "18",
            "medium-fine": "24",
            "medium": "27",
            "medium-coarse": "29",
            "coarse": "31",
        }
    },
    "Fellow Ode Gen 1": {
        "brand": "Fellow",
        "model": "Ode Gen 1",
        "burr_type": "64mm Flat Stainless Steel",
        "pourover_range": "1.0 - 3.0",
        "mappings": {
            "fine": "1.0",
            "medium-fine": "2.0",
            "medium": "2.2",
            "medium-coarse": "3.0",
            "coarse": "3.2",
        }
    },
    "Fellow Ode Gen 2": {
        "brand": "Fellow",
        "model": "Ode Gen 2",
        "burr_type": "64mm Gen 2 Flat Burrs",
        "pourover_range": "3.0 - 6.0",
        "mappings": {
            "fine": "3.1",
            "medium-fine": "4.1",
            "medium": "5.0",
            "medium-coarse": "5.2",
            "coarse": "6.1",
        }
    },
    "Fellow Opus": {
        "brand": "Fellow",
        "model": "Opus",
        "burr_type": "40mm C-Six Conical",
        "pourover_range": "4.0 - 7.0",
        "mappings": {
            "fine": "4.0",
            "medium-fine": "5.2",
            "medium": "6.0",
            "medium-coarse": "6.2",
            "coarse": "7.1",
        }
    },
    "Eureka Mignon Crono": {
        "brand": "Eureka",
        "model": "Mignon Crono / Filtro",
        "burr_type": "50mm Flat Steel",
        "pourover_range": "2.0 - 4.5",
        "mappings": {
            "fine": "2.0",
            "medium-fine": "3.0",
            "medium": "3.5",
            "medium-coarse": "4.0",
            "coarse": "4.8",
        }
    },
    "Wilfa Svart Aroma": {
        "brand": "Wilfa",
        "model": "Svart Aroma",
        "burr_type": "Conical Steel",
        "pourover_range": "Aeropress to Filter",
        "mappings": {
            "fine": "Aeropress dot 2",
            "medium-fine": "Aeropress right dot",
            "medium": "Filter left dot",
            "medium-coarse": "Filter right dot",
            "coarse": "French Press",
        }
    },
    "Niche Zero": {
        "brand": "Niche",
        "model": "Zero",
        "burr_type": "63mm Mazzer Kony Conical",
        "pourover_range": "35 - 50",
        "mappings": {
            "fine": "32",
            "medium-fine": "40",
            "medium": "45",
            "medium-coarse": "50",
            "coarse": "55",
        }
    },
    "Mahlkonig EK43": {
        "brand": "Mahlkonig",
        "model": "EK43 / EK43S",
        "burr_type": "98mm Cast Steel Flat Burrs",
        "pourover_range": "8.0 - 12.0",
        "mappings": {
            "fine": "7.5",
            "medium-fine": "9.0",
            "medium": "10.0",
            "medium-coarse": "11.0",
            "coarse": "12.5",
        }
    },
    "Mahlkonig X54": {
        "brand": "Mahlkonig",
        "model": "X54",
        "burr_type": "54mm Special Steel Flat Burrs",
        "pourover_range": "18 - 28",
        "mappings": {
            "fine": "16",
            "medium-fine": "22",
            "medium": "25",
            "medium-coarse": "28",
            "coarse": "32",
        }
    },
    "Porlex Mini II": {
        "brand": "Porlex",
        "model": "Mini II",
        "burr_type": "Ceramic Conical",
        "pourover_range": "7 - 11 clicks",
        "mappings": {
            "fine": "6 clicks",
            "medium-fine": "8 clicks",
            "medium": "9 clicks",
            "medium-coarse": "11 clicks",
            "coarse": "13 clicks",
        }
    },
    "DF64 Gen 2": {
        "brand": "Turin",
        "model": "DF64 Gen 2",
        "burr_type": "64mm DLC Flat Burrs",
        "pourover_range": "50 - 75",
        "mappings": {
            "fine": "45",
            "medium-fine": "60",
            "medium": "68",
            "medium-coarse": "75",
            "coarse": "85",
        }
    },
    "Option-O Lagom Mini": {
        "brand": "Option-O",
        "model": "Lagom Mini",
        "burr_type": "48mm Moonshine Conical",
        "pourover_range": "8 - 14 numbers",
        "mappings": {
            "fine": "7",
            "medium-fine": "10",
            "medium": "12",
            "medium-coarse": "14",
            "coarse": "16",
        }
    }
}


GRINDER_DATABASE = GRINDER_CATALOGUE


def get_all_grinders() -> Dict[str, Dict[str, Any]]:
    return GRINDER_CATALOGUE


def _normalize_name(text: str) -> str:
    """Strip non-alphanumeric chars for robust matching (e.g. '1zpresso jmax' -> '1zpressojmax')."""
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def map_grind_setting(grinder_query: str, relative_description: str) -> Optional[str]:
    """Finds best matching grinder model and resolves exact click/number setting."""
    if not grinder_query:
        return None

    query_raw = grinder_query.strip()
    query_lower = query_raw.lower()
    query_norm = _normalize_name(query_raw)
    desc_lower = (relative_description or "").lower()

    # Determine relative category
    cat = "medium-fine"
    if "medium-coarse" in desc_lower or "coarse" in desc_lower:
        cat = "medium-coarse" if "medium-coarse" in desc_lower else "coarse"
    elif "fine" in desc_lower and "medium" not in desc_lower:
        cat = "fine"
    elif "medium" in desc_lower and "fine" not in desc_lower:
        cat = "medium"

    # 1. Direct substring matching against catalogue key or model
    for name, data in GRINDER_CATALOGUE.items():
        name_lower = name.lower()
        model_lower = data.get("model", "").lower()
        if name_lower in query_lower or model_lower in query_lower or query_lower in name_lower:
            setting = data["mappings"].get(cat, data["mappings"].get("medium-fine"))
            return f"{name}: {setting} ({data['pourover_range']})"

    # 2. Normalized matching (handles variations in spaces/hyphens like '1zpresso jmax', 'j-max', 'k6', 'c40')
    if query_norm:
        for name, data in GRINDER_CATALOGUE.items():
            name_norm = _normalize_name(name)
            model_norm = _normalize_name(data.get("model", ""))
            aliases_norm = [_normalize_name(a) for a in data.get("aliases", [])]

            # Direct match against normalized name
            if query_norm == name_norm or (len(query_norm) >= 3 and query_norm in name_norm) or name_norm in query_norm:
                setting = data["mappings"].get(cat, data["mappings"].get("medium-fine"))
                return f"{name}: {setting} ({data['pourover_range']})"

            # Direct match against normalized model
            if query_norm == model_norm or (len(query_norm) >= 3 and query_norm in model_norm) or model_norm in query_norm:
                setting = data["mappings"].get(cat, data["mappings"].get("medium-fine"))
                return f"{name}: {setting} ({data['pourover_range']})"

            # Match against registered aliases
            for a_norm in aliases_norm:
                if query_norm == a_norm or (len(query_norm) >= 3 and query_norm in a_norm) or (len(a_norm) >= 3 and a_norm in query_norm):
                    setting = data["mappings"].get(cat, data["mappings"].get("medium-fine"))
                    return f"{name}: {setting} ({data['pourover_range']})"

    return None

