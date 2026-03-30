import uuid
from datetime import datetime, timezone
import enum

from sqlalchemy import DateTime, String, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EINStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    RECEIVED = "received"
    FAILED = "failed"


class EINApplication(Base):
    __tablename__ = "ein_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, unique=True
    )
    status: Mapped[EINStatus] = mapped_column(SAEnum(EINStatus), default=EINStatus.PENDING)
    ein_number: Mapped[str | None] = mapped_column(String(20))
    responsible_party_name: Mapped[str] = mapped_column(String(255), nullable=False)
    responsible_party_ssn_last4: Mapped[str | None] = mapped_column(String(4))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    order: Mapped["Order"] = relationship(back_populates="ein_application")  # noqa: F821
