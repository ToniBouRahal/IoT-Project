from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Threshold, User
from app.schemas.threshold import ThresholdOut, ThresholdUpdate
from app.services.commands import publish_threshold_update

router = APIRouter(prefix="/devices", tags=["thresholds"])


@router.get("/{device_id}/thresholds", response_model=ThresholdOut)
async def get_thresholds(
    device_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Threshold).where(Threshold.device_id == device_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Thresholds not found for device")
    return row


@router.put("/{device_id}/thresholds", response_model=ThresholdOut)
async def update_thresholds(
    device_id: str,
    body: ThresholdUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Threshold).where(Threshold.device_id == device_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Thresholds not found for device")

    updates = body.model_dump(exclude_none=True)
    for field, value in updates.items():
        setattr(row, field, value)

    await db.commit()
    await db.refresh(row)

    publish_threshold_update(device_id, ThresholdOut.model_validate(row).model_dump(exclude={"device_id"}))
    return row
