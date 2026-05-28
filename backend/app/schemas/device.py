import uuid
from datetime import datetime
from pydantic import BaseModel


class DeviceOut(BaseModel):
    device_id: str
    name: str
    created_at: datetime
    last_seen: datetime | None
    armed: bool = False
    threat: str = "Safe"
    risk_score: float = 0.0
    # Last sensor values — populated from device_state.last_reading
    temperature_c: float | None = None
    humidity_percent: float | None = None
    light: int | None = None
    flame_detected: bool | None = None
    motion_detected: bool | None = None

    model_config = {"from_attributes": True}


class SensorReadingOut(BaseModel):
    id: int
    device_id: str
    timestamp: datetime
    light: int | None
    flame_detected: bool | None
    temperature_c: float | None
    humidity_percent: float | None
    motion_detected: bool | None
    armed: bool | None
    threat: str | None
    risk_score: float | None

    model_config = {"from_attributes": True}


class EventOut(BaseModel):
    id: uuid.UUID
    device_id: str
    event_type: str
    risk_score: float
    sensor_snapshot: dict
    created_at: datetime
    alert_sent: bool

    model_config = {"from_attributes": True}
