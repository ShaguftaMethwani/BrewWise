from typing import List, Optional
from pydantic import BaseModel


class EquipmentItem(BaseModel):
    id: str
    category: str  # "dripper" or "grinder"
    brand: str
    model: str
    geometry: Optional[str] = None  # conical, flat_bottom
    description: Optional[str] = None
    default_ratio: Optional[str] = "1:16"


SEED_DRIPPERS = [
    EquipmentItem(
        id="hario-v60",
        category="dripper",
        brand="Hario",
        model="V60 (02)",
        geometry="conical",
        description="Conical dripper with 60-degree angle and spiral ribs for fast drawdown and bright acidity."
    ),
    EquipmentItem(
        id="kalita-wave",
        category="dripper",
        brand="Kalita",
        model="Wave 185",
        geometry="flat_bottom",
        description="Flat-bottom dripper with three restriction holes encouraging even extraction and sweet body."
    ),
    EquipmentItem(
        id="origami",
        category="dripper",
        brand="Origami",
        model="Dripper M",
        geometry="conical",
        description="Versatile ceramic dripper compatible with both conical and wave filters."
    ),
    EquipmentItem(
        id="april-brewer",
        category="dripper",
        brand="April",
        model="Glass Brewer",
        geometry="flat_bottom",
        description="Specialty competition flat brewer focused on floral clarity and high balance."
    ),
    EquipmentItem(
        id="fellow-stagg-x",
        category="dripper",
        brand="Fellow",
        model="Stagg [X]",
        geometry="flat_bottom",
        description="Steep-walled vacuum insulated brewer ensuring consistent brewing temperatures."
    )
]

SEED_GRINDERS = [
    EquipmentItem(
        id="comandante-c40",
        category="grinder",
        brand="Comandante",
        model="C40 MK4 Nitro Blade",
        description="Benchmark manual grinder with precision burrs. Recommended pour-over setting: 22-28 clicks."
    ),
    EquipmentItem(
        id="1zpresso-jx-pro",
        category="grinder",
        brand="1Zpresso",
        model="JX-Pro",
        description="High-precision manual grinder with top adjustment ring. Recommended pour-over setting: 3.2 - 3.6 rotations."
    ),
    EquipmentItem(
        id="baratza-encore",
        category="grinder",
        brand="Baratza",
        model="Encore / ESP",
        description="Standard entry electric burr grinder. Recommended setting: 14 - 18."
    ),
    EquipmentItem(
        id="fellow-ode-gen2",
        category="grinder",
        brand="Fellow",
        model="Ode Gen 2",
        description="Flat burr dedicated filter grinder. Recommended pour-over setting: 4.1 - 5.2."
    ),
    EquipmentItem(
        id="timemore-c2",
        category="grinder",
        brand="Timemore",
        model="Chestnut C2 / C3",
        description="Affordable high quality stainless burr manual grinder. Recommended setting: 15-18 clicks."
    )
]


class EquipmentCatalogue:
    @staticmethod
    def get_drippers(query: Optional[str] = None) -> List[EquipmentItem]:
        if not query:
            return SEED_DRIPPERS
        q = query.lower()
        return [d for d in SEED_DRIPPERS if q in d.brand.lower() or q in d.model.lower()]

    @staticmethod
    def get_grinders(query: Optional[str] = None) -> List[EquipmentItem]:
        if not query:
            return SEED_GRINDERS
        q = query.lower()
        return [g for g in SEED_GRINDERS if q in g.brand.lower() or q in g.model.lower()]
