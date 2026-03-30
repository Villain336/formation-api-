import uuid
from datetime import datetime
from pydantic import BaseModel

from app.models.member import MemberRole


class MemberCreate(BaseModel):
    role: MemberRole
    full_name: str
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    ssn_last4: str | None = None
    ownership_percentage: float | None = None
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    zip_code: str
    country: str = "US"


class MemberResponse(BaseModel):
    id: uuid.UUID
    role: MemberRole
    full_name: str
    title: str | None
    email: str | None
    ownership_percentage: float | None
    city: str
    state: str
    created_at: datetime

    model_config = {"from_attributes": True}
