from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Device, User
from app.services.commands import publish_arm, publish_disarm

router = APIRouter(prefix="/devices", tags=["commands"])


async def _require_device(device_id: str, db: AsyncSession):
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("/{device_id}/arm")
async def arm_device(
    device_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    await _require_device(device_id, db)
    publish_arm(device_id)
    return {"status": "arm command sent", "device_id": device_id}


@router.post("/{device_id}/disarm")
async def disarm_device(
    device_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    await _require_device(device_id, db)
    publish_disarm(device_id)
    return {"status": "disarm command sent", "device_id": device_id}
