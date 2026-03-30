from __future__ import annotations
from typing import Optional, List

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
    filed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ComplianceTaskUpdate(BaseModel):
    status: Optional[ComplianceStatus] = None
    notes: Optional[str] = None
