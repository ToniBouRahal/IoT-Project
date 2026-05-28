import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    state: Mapped["DeviceState"] = relationship("DeviceState", back_populates="device", uselist=False)
    thresholds: Mapped["Threshold"] = relationship("Threshold", back_populates="device", uselist=False)
