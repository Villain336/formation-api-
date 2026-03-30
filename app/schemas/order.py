from __future__ import annotations
from typing import Optional, List

import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.order import OrderStatus, ProcessingSpeed
from app.schemas.member import MemberCreate, MemberResponse


class OrderCreate(BaseModel):
    entity_type: str = Field(..., description="llc, corporation, s_corp, nonprofit, lp, llp")
    state_of_formation: str = Field(..., min_length=2, max_length=2, description="Two-letter state code")
    business_name: str = Field(..., min_length=1, max_length=255)
    business_name_alt1: Optional[str] = None
    business_name_alt2: Optional[str] = None
    business_purpose: Optional[str] = None
    business_address_line1: str
    business_address_line2: Optional[str] = None
    business_city: str
    business_state: str = Field(..., min_length=2, max_length=2)
    business_zip: str
    processing_speed: ProcessingSpeed = ProcessingSpeed.STANDARD
    include_registered_agent: bool = True
    include_ein: bool = False
    include_operating_agreement: bool = False
    members: list[MemberCreate] = Field(default_factory=list)


class OrderUpdate(BaseModel):
    business_name: Optional[str] = None
    business_name_alt1: Optional[str] = None
    business_name_alt2: Optional[str] = None
    business_purpose: Optional[str] = None
    business_address_line1: Optional[str] = None
    business_address_line2: Optional[str] = None
    business_city: Optional[str] = None
    business_state: Optional[str] = None
    business_zip: Optional[str] = None
    processing_speed: Optional[ProcessingSpeed] = None
    include_registered_agent: Optional[bool] = None
    include_ein: Optional[bool] = None
    include_operating_agreement: Optional[bool] = None


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    status: OrderStatus
    entity_type: str
    state_of_formation: str
    business_name: str
    business_name_alt1: Optional[str]
    business_name_alt2: Optional[str]
    business_purpose: Optional[str]
    business_address_line1: str
    business_address_line2: Optional[str]
    business_city: str
    business_state: str
    business_zip: str
    processing_speed: ProcessingSpeed
    include_registered_agent: bool
    include_ein: bool
    include_operating_agreement: bool
    state_fee: int
    service_fee: int
    expedited_fee: int
    registered_agent_fee: int
    total_amount: int
    state_filing_number: Optional[str]
    filed_at: Optional[datetime]
    effective_date: Optional[datetime]
    rejection_reason: Optional[str]
    members: list[MemberResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]
    total: int
    page: int
    per_page: int


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    notes: Optional[str] = None
    state_filing_number: Optional[str] = None
    rejection_reason: Optional[str] = None


class PricingResponse(BaseModel):
    state_fee: int
    service_fee: int
    expedited_fee: int
    registered_agent_fee: int
    total_amount: int
    currency: str = "usd"
    breakdown: dict


class NameCheckRequest(BaseModel):
    business_name: str
    state: str = Field(..., min_length=2, max_length=2)
    entity_type: str


class NameCheckResponse(BaseModel):
    available: bool
    business_name: str
    state: str
    suggestions: list[str] = []
    naming_rules: Optional[dict] = None
