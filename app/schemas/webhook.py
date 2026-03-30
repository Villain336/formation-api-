from __future__ import annotations
from typing import List, Optional

import uuid
from datetime import datetime
from pydantic import BaseModel


class WebhookEndpointCreate(BaseModel):
    url: str
    events: List[str]  # ["order.status_changed", "order.completed", "ein.received"]


class WebhookEndpointResponse(BaseModel):
    id: uuid.UUID
    url: str
    secret: Optional[str] = None  # Only on creation
    events: List[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    payload: dict
    status_code: Optional[int]
    attempts: int
    delivered_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
