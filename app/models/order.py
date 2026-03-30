from __future__ import annotations

import typing
from typing import Optional, List

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, ForeignKey, JSON, Index, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base


class OrderStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    PROCESSING = "processing"
    FILED = "filed"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ProcessingSpeed(str, enum.Enum):
    STANDARD = "standard"
    EXPEDITED = "expedited"
    RUSH = "rush"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    order_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus), default=OrderStatus.DRAFT, nullable=False, index=True
    )

    # Entity details
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # llc, corporation, etc.
    state_of_formation: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_name_alt1: Mapped[Optional[str]] = mapped_column(String(255))
    business_name_alt2: Mapped[Optional[str]] = mapped_column(String(255))
    business_purpose: Mapped[Optional[str]] = mapped_column(Text)
    business_address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    business_address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    business_city: Mapped[str] = mapped_column(String(100), nullable=False)
    business_state: Mapped[str] = mapped_column(String(2), nullable=False)
    business_zip: Mapped[str] = mapped_column(String(10), nullable=False)
    business_country: Mapped[str] = mapped_column(String(2), default="US")

    # Formation options
    processing_speed: Mapped[ProcessingSpeed] = mapped_column(
        SAEnum(ProcessingSpeed), default=ProcessingSpeed.STANDARD
    )
    include_registered_agent: Mapped[bool] = mapped_column(default=True)
    include_ein: Mapped[bool] = mapped_column(default=False)
    include_operating_agreement: Mapped[bool] = mapped_column(default=False)

    # Pricing in cents
    state_fee: Mapped[int] = mapped_column(Integer, default=0)
    service_fee: Mapped[int] = mapped_column(Integer, default=0)
    expedited_fee: Mapped[int] = mapped_column(Integer, default=0)
    registered_agent_fee: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[int] = mapped_column(Integer, default=0)

    # Filing info
    state_filing_number: Mapped[Optional[str]] = mapped_column(String(100))
    filed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    effective_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Metadata
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="orders")  # noqa: F821
    members: Mapped[list["Member"]] = relationship(back_populates="order", cascade="all, delete")  # noqa: F821
    documents: Mapped[list["Document"]] = relationship(back_populates="order")  # noqa: F821
    payments: Mapped[list["Payment"]] = relationship(back_populates="order")  # noqa: F821
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        back_populates="order", cascade="all, delete"
    )
    ein_application: Mapped[Optional["EINApplication"]] = relationship(back_populates="order")  # noqa: F821
    registered_agent: Mapped[Optional["RegisteredAgentService"]] = relationship(back_populates="order")  # noqa: F821
    compliance_tasks: Mapped[list["ComplianceTask"]] = relationship(back_populates="order")  # noqa: F821

    __table_args__ = (
        Index("ix_orders_user_status", "user_id", "status"),
        Index("ix_orders_state_status", "state_of_formation", "status"),
    )


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    from_status: Mapped[Optional[str]] = mapped_column(String(50))
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    order: Mapped["Order"] = relationship(back_populates="status_history")
