import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(String(128), ForeignKey("devices.device_id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sensor_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    alert_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="event")
