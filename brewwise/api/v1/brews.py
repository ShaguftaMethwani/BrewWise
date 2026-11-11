import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from brewwise.db.session import get_db
from brewwise.models.brew_log import BrewLogModel
from brewwise.models.user import UserModel
from brewwise.schemas.brew import (
    BrewLogCreate,
    BrewLogResponse,
    BrewLogFeedbackUpdate,
    AdjustmentRecommendation
)
from brewwise.services.auth.jwt_service import get_current_user_optional
from brewwise.services.feedback.analyser import FeedbackAnalyser

router = APIRouter(prefix="/brews", tags=["Brew Logs & Feedback"])


@router.post("", response_model=BrewLogResponse)
async def log_brew(
    data: BrewLogCreate,
    user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    # Analyze brew sensory metrics to determine barista adjustments
    adjustments = FeedbackAnalyser.analyse(data)

    brew = BrewLogModel(
        id=str(uuid.uuid4()),
        user_id=user.id if user else None,
        recipe_id=data.recipe_id,
        coffee_profile_id=data.coffee_profile_id,
        dripper=data.dripper,
        grinder=data.grinder,
        actual_dose_g=data.actual_dose_g,
        actual_water_g=data.actual_water_g,
        actual_grind_setting=data.actual_grind_setting,
        actual_temp_c=data.actual_temp_c,
        actual_brew_time_seconds=data.actual_brew_time_seconds,
        sourness=data.sourness,
        bitterness=data.bitterness,
        sweetness=data.sweetness,
        body=data.body,
        overall_satisfaction=data.overall_satisfaction,
        drawdown_speed=data.drawdown_speed,
        flavour_notes=data.flavour_notes,
        adjustments=adjustments.model_dump(mode="json")
    )
    db.add(brew)
    await db.commit()
    await db.refresh(brew)

    return BrewLogResponse(
        id=brew.id,
        user_id=brew.user_id,
        recipe_id=brew.recipe_id,
        coffee_profile_id=brew.coffee_profile_id,
        brewed_at=brew.brewed_at,
        dripper=brew.dripper,
        grinder=brew.grinder,
        actual_dose_g=brew.actual_dose_g,
        actual_water_g=brew.actual_water_g,
        actual_grind_setting=brew.actual_grind_setting,
        actual_temp_c=brew.actual_temp_c,
        actual_brew_time_seconds=brew.actual_brew_time_seconds,
        sourness=brew.sourness,
        bitterness=brew.bitterness,
        sweetness=brew.sweetness,
        body=brew.body,
        overall_satisfaction=brew.overall_satisfaction,
        drawdown_speed=brew.drawdown_speed,
        flavour_notes=brew.flavour_notes,
        adjustments=adjustments,
        created_at=brew.created_at
    )


@router.get("", response_model=List[BrewLogResponse])
async def list_brews(
    coffee_profile_id: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    user: Optional[UserModel] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(BrewLogModel).order_by(BrewLogModel.brewed_at.desc()).limit(limit)
    if user:
        stmt = stmt.where(BrewLogModel.user_id == user.id)
    if coffee_profile_id:
        stmt = stmt.where(BrewLogModel.coffee_profile_id == coffee_profile_id)

    res = await db.execute(stmt)
    items = res.scalars().all()

    return [
        BrewLogResponse(
            id=b.id,
            user_id=b.user_id,
            recipe_id=b.recipe_id,
            coffee_profile_id=b.coffee_profile_id,
            brewed_at=b.brewed_at,
            dripper=b.dripper,
            grinder=b.grinder,
            actual_dose_g=b.actual_dose_g,
            actual_water_g=b.actual_water_g,
            actual_grind_setting=b.actual_grind_setting,
            actual_temp_c=b.actual_temp_c,
            actual_brew_time_seconds=b.actual_brew_time_seconds,
            sourness=b.sourness,
            bitterness=b.bitterness,
            sweetness=b.sweetness,
            body=b.body,
            overall_satisfaction=b.overall_satisfaction,
            drawdown_speed=b.drawdown_speed,
            flavour_notes=b.flavour_notes,
            adjustments=AdjustmentRecommendation(**b.adjustments) if b.adjustments else None,
            created_at=b.created_at
        )
        for b in items
    ]


@router.get("/{brew_id}", response_model=BrewLogResponse)
async def get_brew(brew_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(BrewLogModel).where(BrewLogModel.id == brew_id)
    res = await db.execute(stmt)
    b = res.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Brew log not found")

    return BrewLogResponse(
        id=b.id,
        user_id=b.user_id,
        recipe_id=b.recipe_id,
        coffee_profile_id=b.coffee_profile_id,
        brewed_at=b.brewed_at,
        dripper=b.dripper,
        grinder=b.grinder,
        actual_dose_g=b.actual_dose_g,
        actual_water_g=b.actual_water_g,
        actual_grind_setting=b.actual_grind_setting,
        actual_temp_c=b.actual_temp_c,
        actual_brew_time_seconds=b.actual_brew_time_seconds,
        sourness=b.sourness,
        bitterness=b.bitterness,
        sweetness=b.sweetness,
        body=b.body,
        overall_satisfaction=b.overall_satisfaction,
        drawdown_speed=b.drawdown_speed,
        flavour_notes=b.flavour_notes,
        adjustments=AdjustmentRecommendation(**b.adjustments) if b.adjustments else None,
        created_at=b.created_at
    )


@router.post("/{brew_id}/feedback", response_model=BrewLogResponse)
async def update_brew_feedback(
    brew_id: str,
    feedback: BrewLogFeedbackUpdate,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(BrewLogModel).where(BrewLogModel.id == brew_id)
    res = await db.execute(stmt)
    brew = res.scalar_one_or_none()
    if not brew:
        raise HTTPException(status_code=404, detail="Brew log not found")

    update_dict = feedback.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        if v is not None:
            setattr(brew, k, v)

    # Re-calculate adjustments based on updated feedback
    adjustments = FeedbackAnalyser.analyse(brew)
    brew.adjustments = adjustments.model_dump(mode="json")

    await db.commit()
    await db.refresh(brew)

    return BrewLogResponse(
        id=brew.id,
        user_id=brew.user_id,
        recipe_id=brew.recipe_id,
        coffee_profile_id=brew.coffee_profile_id,
        brewed_at=brew.brewed_at,
        dripper=brew.dripper,
        grinder=brew.grinder,
        actual_dose_g=brew.actual_dose_g,
        actual_water_g=brew.actual_water_g,
        actual_grind_setting=brew.actual_grind_setting,
        actual_temp_c=brew.actual_temp_c,
        actual_brew_time_seconds=brew.actual_brew_time_seconds,
        sourness=brew.sourness,
        bitterness=brew.bitterness,
        sweetness=brew.sweetness,
        body=brew.body,
        overall_satisfaction=brew.overall_satisfaction,
        drawdown_speed=brew.drawdown_speed,
        flavour_notes=brew.flavour_notes,
        adjustments=adjustments,
        created_at=brew.created_at
    )
