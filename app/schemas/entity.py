from __future__ import annotations
from typing import List, Optional

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
    expedited_fee: Optional[int]
    name_reservation_fee: Optional[int]
    standard_processing_days: int
    expedited_processing_days: Optional[int]
    requires_registered_agent: bool
    requires_operating_agreement: bool
    requires_publication: bool
    requires_initial_report: bool
    min_members: int
    min_directors: Optional[int]
    annual_report_fee: Optional[int]
    annual_report_month: Optional[int]
    franchise_tax: Optional[int]
    filing_agency: str
    filing_agency_url: Optional[str]
    online_filing_available: bool
    naming_rules: Optional[dict]
    required_documents: Optional[dict]

    model_config = {"from_attributes": True}


class StateListResponse(BaseModel):
    states: List[StateRequirementResponse]
    total: int
