from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel


class WebhookEndpointCreate(BaseModel):
    url: str
    events: list[str]  # ["order.status_changed", "order.completed", "ein.received"]


class WebhookEndpointResponse(BaseModel):
    id: uuid.UUID
    url: str
    secret: str | None = None  # Only on creation
    events: list[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    payload: dict
    status_code: int | None
    attempts: int
    delivered_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
