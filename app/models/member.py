from __future__ import annotations

from typing import Optional

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, ForeignKey, Numeric, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base


class MemberRole(str, enum.Enum):
    OWNER = "owner"
    MEMBER = "member"
    MANAGER = "manager"
    ORGANIZER = "organizer"
    REGISTERED_AGENT = "registered_agent"
    DIRECTOR = "director"
    OFFICER = "officer"
    INCORPORATOR = "incorporator"


class Member(Base):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    role: Mapped[MemberRole] = mapped_column(SAEnum(MemberRole), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(100))  # CEO, President, etc.
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    ssn_last4: Mapped[Optional[str]] = mapped_column(String(4))  # For EIN application
    ownership_percentage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    country: Mapped[str] = mapped_column(String(2), default="US")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    order: Mapped["Order"] = relationship(back_populates="members")  # noqa: F821
