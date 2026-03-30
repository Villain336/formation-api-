import uuid
from datetime import datetime, date, timezone
import enum

from sqlalchemy import DateTime, Date, Integer, String, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RAStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class RegisteredAgentService(Base):
    __tablename__ = "registered_agent_services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    status: Mapped[RAStatus] = mapped_column(SAEnum(RAStatus), default=RAStatus.PENDING)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    renewal_date: Mapped[date] = mapped_column(Date, nullable=False)
    annual_fee: Mapped[int] = mapped_column(Integer, nullable=False)  # cents
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    order: Mapped["Order"] = relationship(back_populates="registered_agent")  # noqa: F821
