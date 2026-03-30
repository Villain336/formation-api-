import uuid
from datetime import datetime, date
from pydantic import BaseModel

from app.models.compliance import ComplianceType, ComplianceStatus


class ComplianceTaskResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    task_type: ComplianceType
    status: ComplianceStatus
    due_date: date
    state: str
    description: str
    reminder_sent: bool
    filed_at: datetime | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ComplianceTaskUpdate(BaseModel):
    status: ComplianceStatus | None = None
    notes: str | None = None
