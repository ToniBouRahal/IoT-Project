from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Device, SensorReading, Event, DeviceState, User
from app.schemas.device import DeviceOut, SensorReadingOut, EventOut

router = APIRouter(prefix="/devices", tags=["devices"])


def _build_out(d: Device, state: DeviceState | None) -> DeviceOut:
    lr = state.last_reading or {} if state else {}
    return DeviceOut(
        device_id=d.device_id,
        name=d.name,
        created_at=d.created_at,
        last_seen=d.last_seen,
        armed=state.armed if state else False,
        threat=state.threat if state else "Safe",
        risk_score=state.risk_score if state else 0.0,
        temperature_c=lr.get("temperature_c"),
        humidity_percent=lr.get("humidity_percent"),
        light=lr.get("light"),
        flame_detected=lr.get("flame_detected"),
        motion_detected=lr.get("motion_detected"),
    )


@router.get("", response_model=list[DeviceOut])
async def list_devices(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Device))
    devices = result.scalars().all()
    out = []
    for d in devices:
        state_res = await db.execute(select(DeviceState).where(DeviceState.device_id == d.device_id))
        state = state_res.scalar_one_or_none()
        out.append(_build_out(d, state))
    return out


@router.get("/{device_id}/latest", response_model=DeviceOut)
async def get_latest(
    device_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    state_res = await db.execute(select(DeviceState).where(DeviceState.device_id == device_id))
    state = state_res.scalar_one_or_none()
    return _build_out(device, state)


@router.get("/{device_id}/readings", response_model=list[SensorReadingOut])
async def get_readings(
    device_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    result = await db.execute(
        select(SensorReading)
        .where(SensorReading.device_id == device_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


@router.get("/{device_id}/events", response_model=list[EventOut])
async def get_events(
    device_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    result = await db.execute(
        select(Event)
        .where(Event.device_id == device_id)
        .order_by(Event.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()
