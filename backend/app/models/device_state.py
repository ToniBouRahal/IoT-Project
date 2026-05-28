from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DeviceState(Base):
    __tablename__ = "device_state"

    device_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("devices.device_id"), primary_key=True
    )
    armed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    threat: Mapped[str] = mapped_column(String(32), nullable=False, default="Safe")
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_reading: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    device: Mapped["Device"] = relationship("Device", back_populates="state")
