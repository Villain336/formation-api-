from __future__ import annotations
from typing import Optional

import uuid
from datetime import datetime
from pydantic import BaseModel

from app.models.payment import PaymentStatus


class CreatePaymentIntent(BaseModel):
    order_id: uuid.UUID


class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str


class PaymentResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    stripe_payment_intent_id: Optional[str]
    amount: int
    currency: str
    status: PaymentStatus
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
