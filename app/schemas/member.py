from __future__ import annotations
from typing import Optional

import uuid
from datetime import datetime
from pydantic import BaseModel

from app.models.member import MemberRole


class MemberCreate(BaseModel):
    role: MemberRole
    full_name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    ssn_last4: Optional[str] = None
    ownership_percentage: Optional[float] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str = "US"


class MemberResponse(BaseModel):
    id: uuid.UUID
    role: MemberRole
    full_name: str
    title: Optional[str]
    email: Optional[str]
    ownership_percentage: Optional[float]
    city: str
    state: str
    created_at: datetime

    model_config = {"from_attributes": True}
