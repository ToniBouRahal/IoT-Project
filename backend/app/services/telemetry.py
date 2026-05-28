from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models import Device, SensorReading, DeviceState
from app.schemas.telemetry import TelemetryPayload


async def ensure_device(db: AsyncSession, device_id: str) -> Device:
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()
    if device is None:
        device = Device(device_id=device_id, name=device_id)
        db.add(device)
        await db.flush()
    return device


async def save_telemetry(db: AsyncSession, payload: TelemetryPayload):
    device = await ensure_device(db, payload.device_id)
    device.last_seen = datetime.now(timezone.utc)

    reading = SensorReading(
        device_id=payload.device_id,
        timestamp=payload.timestamp,
        light=payload.light,
        flame_detected=payload.flame_detected,
        temperature_c=payload.temperature_c,
        humidity_percent=payload.humidity_percent,
        motion_detected=payload.motion_detected,
        armed=payload.armed,
        threat=payload.threat,
        risk_score=payload.risk_score,
    )
    db.add(reading)

    # Upsert device_state
    stmt = (
        pg_insert(DeviceState)
        .values(
            device_id=payload.device_id,
            armed=payload.armed or False,
            threat=payload.threat or "Safe",
            risk_score=payload.risk_score or 0.0,
            last_reading=payload.model_dump(mode="json"),
            updated_at=datetime.now(timezone.utc),
        )
        .on_conflict_do_update(
            index_elements=["device_id"],
            set_={
                "armed": payload.armed or False,
                "threat": payload.threat or "Safe",
                "risk_score": payload.risk_score or 0.0,
                "last_reading": payload.model_dump(mode="json"),
                "updated_at": datetime.now(timezone.utc),
            },
        )
    )
    await db.execute(stmt)
    await db.commit()
