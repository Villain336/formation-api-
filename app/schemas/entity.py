import uuid
from pydantic import BaseModel


class EntityTypeResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str
    description: str

    model_config = {"from_attributes": True}


class StateRequirementResponse(BaseModel):
    id: uuid.UUID
    state_code: str
    state_name: str
    entity_type: str
    state_filing_fee: int
    expedited_fee: int | None
    name_reservation_fee: int | None
    standard_processing_days: int
    expedited_processing_days: int | None
    requires_registered_agent: bool
    requires_operating_agreement: bool
    requires_publication: bool
    requires_initial_report: bool
    min_members: int
    min_directors: int | None
    annual_report_fee: int | None
    annual_report_month: int | None
    franchise_tax: int | None
    filing_agency: str
    filing_agency_url: str | None
    online_filing_available: bool
    naming_rules: dict | None
    required_documents: dict | None

    model_config = {"from_attributes": True}


class StateListResponse(BaseModel):
    states: list[StateRequirementResponse]
    total: int
