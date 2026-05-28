# Raw sensor readings are retained for 30 days per ADR 0001.
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(128), ForeignKey("devices.device_id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    light: Mapped[int | None] = mapped_column(Integer, nullable=True)
    flame_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    motion_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    armed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    threat: Mapped[str | None] = mapped_column(String(32), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
