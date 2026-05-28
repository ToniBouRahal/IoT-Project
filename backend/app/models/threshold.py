import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Threshold(Base):
    __tablename__ = "thresholds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("devices.device_id"), unique=True, nullable=False
    )
    light_dark_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    flame_fire_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    temp_high_c: Mapped[float] = mapped_column(Float, nullable=False, default=40.0)
    temp_extreme_c: Mapped[float] = mapped_column(Float, nullable=False, default=60.0)
    humidity_low_pct: Mapped[float] = mapped_column(Float, nullable=False, default=30.0)
    fire_confirm_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.8)
    fire_alarm_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    device: Mapped["Device"] = relationship("Device", back_populates="thresholds")
