from __future__ import annotations

import uuid
from datetime import datetime, date, timezone
import enum

from sqlalchemy import DateTime, Date, String, Boolean, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ComplianceType(str, enum.Enum):
    ANNUAL_REPORT = "annual_report"
    FRANCHISE_TAX = "franchise_tax"
    INITIAL_REPORT = "initial_report"
    PUBLICATION = "publication"
    BOI_REPORT = "boi_report"  # Beneficial Ownership Information


class ComplianceStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    DUE = "due"
    OVERDUE = "overdue"
    FILED = "filed"
    NOT_APPLICABLE = "not_applicable"


class ComplianceTask(Base):
    __tablename__ = "compliance_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    task_type: Mapped[ComplianceType] = mapped_column(SAEnum(ComplianceType), nullable=False)
    status: Mapped[ComplianceStatus] = mapped_column(
        SAEnum(ComplianceStatus), default=ComplianceStatus.UPCOMING
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    filed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    order: Mapped["Order"] = relationship(back_populates="compliance_tasks")  # noqa: F821
