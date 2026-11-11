import uuid
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from brewwise.db.session import get_db
from brewwise.services.equipment.catalogue import EquipmentCatalogue, EquipmentItem
from brewwise.models.equipment_profile import UserEquipmentProfileModel
from brewwise.models.user import UserModel
from brewwise.services.auth.jwt_service import get_current_user_optional, get_current_user
from brewwise.services.equipment.grinder_guide import map_grind_setting, GRINDER_CATALOGUE
from brewwise.services.equipment.dripper_guide import get_dripper_details, DRIPPER_CATALOGUE

router = APIRouter(prefix="/equipment", tags=["Equipment"])


class EquipmentProfileCreate(BaseModel):
    name: str = "My Pour-Over Setup"
    dripper: str = "Hario V60"
    grinder: Optional[str] = "Comandante C40"
    filter_type: Optional[str] = "Paper"
    preferred_dose_g: float = 15.0
    preferred_ratio: str = "1:16"
    experience_level: str = "intermediate"
    is_default: bool = False


class EquipmentProfileUpdate(BaseModel):
    name: Optional[str] = None
    dripper: Optional[str] = None
    grinder: Optional[str] = None
    filter_type: Optional[str] = None
    preferred_dose_g: Optional[float] = None
    preferred_ratio: Optional[str] = None
    experience_level: Optional[str] = None
    is_default: Optional[bool] = None


class EquipmentProfileResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    name: str
    dripper: str
    grinder: Optional[str] = None
    filter_type: Optional[str] = None
    preferred_dose_g: float
    preferred_ratio: str
    experience_level: str
    is_default: bool


@router.get("/drippers", response_model=List[EquipmentItem])
async def get_drippers(query: Optional[str] = Query(default=None)):
    return EquipmentCatalogue.get_drippers(query)


@router.get("/grinders", response_model=List[EquipmentItem])
async def get_grinders(query: Optional[str] = Query(default=None)):
    return EquipmentCatalogue.get_grinders(query)


@router.get("/grind-setting")
async def resolve_grind_setting(grinder: str = Query(...), description: str = Query(default="medium-fine")):
    mapped = map_grind_setting(grinder, description)
    return {"grinder": grinder, "description": description, "setting": mapped}


@router.get("/profiles", response_model=List[EquipmentProfileResponse])
async def list_profiles(
    user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    if user:
        stmt = select(UserEquipmentProfileModel).where(UserEquipmentProfileModel.user_id == user.id)
    else:
        # For anonymous users, return global/default profiles
        stmt = select(UserEquipmentProfileModel).where(UserEquipmentProfileModel.user_id.is_(None))

    res = await db.execute(stmt)
    profiles = res.scalars().all()
    return [
        EquipmentProfileResponse(
            id=p.id,
            user_id=p.user_id,
            name=p.name,
            dripper=p.dripper,
            grinder=p.grinder,
            filter_type=p.filter_type,
            preferred_dose_g=p.preferred_dose_g,
            preferred_ratio=p.preferred_ratio,
            experience_level=p.experience_level,
            is_default=p.is_default
        )
        for p in profiles
    ]


@router.post("/profiles", response_model=EquipmentProfileResponse)
async def create_profile(
    data: EquipmentProfileCreate,
    user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    # If is_default is true, un-default other profiles
    if data.is_default and user:
        stmt = select(UserEquipmentProfileModel).where(UserEquipmentProfileModel.user_id == user.id)
        res = await db.execute(stmt)
        for p in res.scalars().all():
            p.is_default = False

    profile = UserEquipmentProfileModel(
        id=str(uuid.uuid4()),
        user_id=user.id if user else None,
        name=data.name,
        dripper=data.dripper,
        grinder=data.grinder,
        filter_type=data.filter_type,
        preferred_dose_g=data.preferred_dose_g,
        preferred_ratio=data.preferred_ratio,
        experience_level=data.experience_level,
        is_default=data.is_default
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return EquipmentProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        dripper=profile.dripper,
        grinder=profile.grinder,
        filter_type=profile.filter_type,
        preferred_dose_g=profile.preferred_dose_g,
        preferred_ratio=profile.preferred_ratio,
        experience_level=profile.experience_level,
        is_default=profile.is_default
    )


@router.put("/profiles/{profile_id}", response_model=EquipmentProfileResponse)
async def update_profile(
    profile_id: str,
    data: EquipmentProfileUpdate,
    user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(UserEquipmentProfileModel).where(UserEquipmentProfileModel.id == profile_id)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if user and profile.user_id and profile.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this profile.")

    update_dict = data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(profile, k, v)

    await db.commit()
    await db.refresh(profile)

    return EquipmentProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        dripper=profile.dripper,
        grinder=profile.grinder,
        filter_type=profile.filter_type,
        preferred_dose_g=profile.preferred_dose_g,
        preferred_ratio=profile.preferred_ratio,
        experience_level=profile.experience_level,
        is_default=profile.is_default
    )


@router.delete("/profiles/{profile_id}")
async def delete_profile(
    profile_id: str,
    user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(UserEquipmentProfileModel).where(UserEquipmentProfileModel.id == profile_id)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if user and profile.user_id and profile.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this profile.")

    await db.delete(profile)
    await db.commit()
    return {"message": "Profile deleted successfully"}
