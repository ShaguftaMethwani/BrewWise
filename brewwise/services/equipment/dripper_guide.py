from typing import Dict, Any, Optional

DRIPPER_CATALOGUE: Dict[str, Dict[str, Any]] = {
    "Hario V60": {
        "geometry": "Conical 60°",
        "flow_rate": "Fast / User-controlled",
        "filter": "Hario V60 01/02 Tabbed/Untabbed Paper",
        "technique": "Spiral concentric pours avoiding outer wall. Allows high acidity and floral clarity."
    },
    "Kalita Wave": {
        "geometry": "Flat-bottom 3-hole",
        "flow_rate": "Moderate / Consistent",
        "filter": "Kalita 155/185 Wave Fluted Paper",
        "technique": "Pulse pours in center to maintain even water level across shallow coffee bed. Delivers rich sweetness and body."
    },
    "Origami Dripper": {
        "geometry": "Conical / Flat hybrid 20-rib",
        "flow_rate": "Fast",
        "filter": "Conical V60 or Kalita Wave Paper",
        "technique": "Fast drawdown promotes vibrant sweetness and complex fruit aromatics."
    },
    "Chemex": {
        "geometry": "Conical Heavy Bonded",
        "flow_rate": "Moderate-Slow",
        "filter": "Chemex Bonded Paper Filter",
        "technique": "Thick filter absorbs coffee oils, producing an exceptionally clean, sediment-free cup."
    },
    "Fellow Stagg [X]": {
        "geometry": "Flat-bottom Steep Wall",
        "flow_rate": "Fast-Medium",
        "filter": "Fellow Stagg [X] Paper Filters",
        "technique": "Insulated double wall retains heat for high extraction yields on light roasts."
    },
    "April Dripper": {
        "geometry": "Flat-bottom Low Bypass",
        "flow_rate": "Predictable / Structured",
        "filter": "April Paper Filters",
        "technique": "Two to three large circular pours for high clarity and sweet fruit acidity."
    },
    "Clever Dripper": {
        "geometry": "Immersion / Pour-over Hybrid",
        "flow_rate": "Drawdown upon release valve",
        "filter": "Size 4 Cone Paper Filters",
        "technique": "Full steep immersion for 2 minutes followed by clean gravity drawdown."
    },
    "AeroPress": {
        "geometry": "Immersion Pressure Extraction",
        "flow_rate": "Plunger applied pressure",
        "filter": "AeroPress Micro Paper or Metal Filter",
        "technique": "Inverted or standard method yielding intense clarity with zero bitterness."
    },
    "Kono Meimon": {
        "geometry": "Conical Low-Rib",
        "flow_rate": "Slow at top, fast at bottom",
        "filter": "Kono or V60 Paper Filter",
        "technique": "Deep bloom extraction enhancing syrupy mouthfeel and sweetness."
    },
    "Orea V3": {
        "geometry": "Flat-bottom Open Base",
        "flow_rate": "Ultra Fast",
        "filter": "Kalita 185 or Sibarist Flat Filter",
        "technique": "High flow rate prevents clogging and bitterness even with ultra-fine grind settings."
    }
}


def get_all_drippers() -> Dict[str, Dict[str, Any]]:
    return DRIPPER_CATALOGUE


def get_dripper_details(dripper_name: str) -> Optional[Dict[str, Any]]:
    for name, data in DRIPPER_CATALOGUE.items():
        if name.lower() in dripper_name.lower() or dripper_name.lower() in name.lower():
            return {"name": name, **data}
    return None
