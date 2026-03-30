"""Filing submission tracking model.

Tracks every filing attempt — which provider handled it, the status,
reference IDs, and the full audit trail of state interactions.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, Boolean, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FilingSubmission(Base):
    """Tracks a filing submission to a state or vendor."""
    __tablename__ = "filing_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )

    # Provider info
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)  # "delaware_direct", "manual", etc.
    provider_type: Mapped[str] = mapped_column(String(20), nullable=False)  # state_direct, vendor, manual
    provider_reference_id: Mapped[Optional[str]] = mapped_column(String(255))  # Provider's tracking ID

    # Status
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued", index=True)
    status_message: Mapped[Optional[str]] = mapped_column(Text)

    # State filing result
    state_filing_number: Mapped[Optional[str]] = mapped_column(String(100))
    formation_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Tracking
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    estimated_completion: Mapped[Optional[str]] = mapped_column(String(100))

    # Admin
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255))  # For manual queue
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    is_expedited: Mapped[bool] = mapped_column(Boolean, default=False)

    # Raw data
    request_payload: Mapped[Optional[dict]] = mapped_column(JSON)
    response_payload: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    order: Mapped["Order"] = relationship()  # noqa: F821
    status_logs: Mapped[list] = relationship("FilingStatusLog", back_populates="submission", cascade="all, delete")

    __table_args__ = (
        Index("ix_filing_submissions_provider_status", "provider_name", "status"),
        Index("ix_filing_submissions_order_attempt", "order_id", "attempt_number"),
    )


class FilingStatusLog(Base):
    """Audit log for every status change on a filing submission."""
    __tablename__ = "filing_status_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("filing_submissions.id"), nullable=False, index=True
    )
    from_status: Mapped[Optional[str]] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    changed_by: Mapped[Optional[str]] = mapped_column(String(255))  # "system", "admin:user@email", "provider:delaware"
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    submission: Mapped["FilingSubmission"] = relationship(back_populates="status_logs")
