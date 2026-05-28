from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event
from app.schemas.telemetry import EventPayload
from app.services.telemetry import ensure_device


async def save_event(db: AsyncSession, payload: EventPayload) -> Event:
    await ensure_device(db, payload.device_id)

    event = Event(
        device_id=payload.device_id,
        event_type=payload.event_type,
        risk_score=payload.risk_score,
        sensor_snapshot=payload.sensor_snapshot,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
