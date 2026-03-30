import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.order import OrderStatus, ProcessingSpeed
from app.schemas.member import MemberCreate, MemberResponse


class OrderCreate(BaseModel):
    entity_type: str = Field(..., description="llc, corporation, s_corp, nonprofit, lp, llp")
    state_of_formation: str = Field(..., min_length=2, max_length=2, description="Two-letter state code")
    business_name: str = Field(..., min_length=1, max_length=255)
    business_name_alt1: str | None = None
    business_name_alt2: str | None = None
    business_purpose: str | None = None
    business_address_line1: str
    business_address_line2: str | None = None
    business_city: str
    business_state: str = Field(..., min_length=2, max_length=2)
    business_zip: str
    processing_speed: ProcessingSpeed = ProcessingSpeed.STANDARD
    include_registered_agent: bool = True
    include_ein: bool = False
    include_operating_agreement: bool = False
    members: list[MemberCreate] = Field(default_factory=list)


class OrderUpdate(BaseModel):
    business_name: str | None = None
    business_name_alt1: str | None = None
    business_name_alt2: str | None = None
    business_purpose: str | None = None
    business_address_line1: str | None = None
    business_address_line2: str | None = None
    business_city: str | None = None
    business_state: str | None = None
    business_zip: str | None = None
    processing_speed: ProcessingSpeed | None = None
    include_registered_agent: bool | None = None
    include_ein: bool | None = None
    include_operating_agreement: bool | None = None


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    status: OrderStatus
    entity_type: str
    state_of_formation: str
    business_name: str
    business_name_alt1: str | None
    business_name_alt2: str | None
    business_purpose: str | None
    business_address_line1: str
    business_address_line2: str | None
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
    state_filing_number: str | None
    filed_at: datetime | None
    effective_date: datetime | None
    rejection_reason: str | None
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
    notes: str | None = None
    state_filing_number: str | None = None
    rejection_reason: str | None = None


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
    naming_rules: dict | None = None
