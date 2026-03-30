from __future__ import annotations

from typing import Optional

import uuid
from datetime import datetime, timezone
import enum

from sqlalchemy import DateTime, Integer, String, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentType(str, enum.Enum):
    ARTICLES_OF_ORGANIZATION = "articles_of_organization"
    ARTICLES_OF_INCORPORATION = "articles_of_incorporation"
    OPERATING_AGREEMENT = "operating_agreement"
    BYLAWS = "bylaws"
    EIN_CONFIRMATION = "ein_confirmation"
    CERTIFICATE_OF_FORMATION = "certificate_of_formation"
    FILED_DOCUMENT = "filed_document"
    ANNUAL_REPORT = "annual_report"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    doc_type: Mapped[DocumentType] = mapped_column(SAEnum(DocumentType), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    order: Mapped["Order"] = relationship(back_populates="documents")  # noqa: F821
