import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EntityType(Base):
    """Supported business entity types."""

    __tablename__ = "entity_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e.g. "llc"
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "LLC"
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StateRequirement(Base):
    """State-specific formation requirements and fees."""

    __tablename__ = "state_requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)  # e.g. "DE"
    state_name: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g. "llc"

    # Fees in cents
    state_filing_fee: Mapped[int] = mapped_column(Integer, nullable=False)
    expedited_fee: Mapped[int | None] = mapped_column(Integer)
    name_reservation_fee: Mapped[int | None] = mapped_column(Integer)

    # Processing
    standard_processing_days: Mapped[int] = mapped_column(Integer, nullable=False)
    expedited_processing_days: Mapped[int | None] = mapped_column(Integer)

    # Requirements
    requires_registered_agent: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_operating_agreement: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_publication: Mapped[bool] = mapped_column(Boolean, default=False)  # NY, AZ, NE
    requires_initial_report: Mapped[bool] = mapped_column(Boolean, default=False)
    min_members: Mapped[int] = mapped_column(Integer, default=1)
    min_directors: Mapped[int | None] = mapped_column(Integer)  # For corps

    # Annual compliance
    annual_report_fee: Mapped[int | None] = mapped_column(Integer)
    annual_report_month: Mapped[int | None] = mapped_column(Integer)  # 1-12
    franchise_tax: Mapped[int | None] = mapped_column(Integer)

    # Filing details
    filing_agency: Mapped[str] = mapped_column(String(200), nullable=False)
    filing_agency_url: Mapped[str | None] = mapped_column(String(500))
    online_filing_available: Mapped[bool] = mapped_column(Boolean, default=False)
    naming_rules: Mapped[dict | None] = mapped_column(JSON)  # Required suffixes, restricted words
    required_documents: Mapped[dict | None] = mapped_column(JSON)  # List of required docs

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
