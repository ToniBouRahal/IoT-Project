from datetime import datetime
from pydantic import BaseModel, Field


class TelemetryPayload(BaseModel):
    device_id: str
    timestamp: datetime
    light: int | None = None
    flame_detected: bool | None = None
    temperature_c: float | None = None
    humidity_percent: float | None = None
    motion_detected: bool | None = None
    armed: bool | None = None
    threat: str | None = None
    risk_score: float | None = Field(None, ge=0.0, le=1.0)


class EventPayload(BaseModel):
    device_id: str
    timestamp: datetime
    event_type: str
    risk_score: float = Field(0.0, ge=0.0, le=1.0)
    sensor_snapshot: dict = {}
