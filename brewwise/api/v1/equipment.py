from typing import List, Optional
from fastapi import APIRouter, Query
from brewwise.services.equipment.catalogue import EquipmentCatalogue, EquipmentItem

router = APIRouter(prefix="/equipment", tags=["Equipment"])


@router.get("/drippers", response_model=List[EquipmentItem])
async def get_drippers(query: Optional[str] = Query(default=None)):
    return EquipmentCatalogue.get_drippers(query)


@router.get("/grinders", response_model=List[EquipmentItem])
async def get_grinders(query: Optional[str] = Query(default=None)):
    return EquipmentCatalogue.get_grinders(query)
