import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(32), nullable=False, default="email")
    recipient: Mapped[str] = mapped_column(String(256), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    event: Mapped["Event"] = relationship("Event", back_populates="alerts")
