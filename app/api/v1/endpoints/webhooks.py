"""Webhook management endpoints."""
from __future__ import annotations
from typing import List

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.webhook import WebhookEndpoint, WebhookEvent
from app.schemas.webhook import WebhookEndpointCreate, WebhookEndpointResponse, WebhookEventResponse

router = APIRouter()

VALID_EVENTS = [
    "order.created",
    "order.status_changed",
    "order.completed",
    "order.rejected",
    "payment.succeeded",
    "payment.failed",
    "ein.received",
    "compliance.due",
    "registered_agent.renewal",
]


@router.post("/endpoints", response_model=WebhookEndpointResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook_endpoint(
    data: WebhookEndpointCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a webhook endpoint to receive event notifications."""
    invalid = set(data.events) - set(VALID_EVENTS)
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid events: {invalid}. Valid: {VALID_EVENTS}")

    secret = f"whsec_{secrets.token_urlsafe(32)}"
    endpoint = WebhookEndpoint(
        user_id=current_user.id,
        url=data.url,
        secret=secret,
        events=data.events,
    )
    db.add(endpoint)
    await db.flush()

    return WebhookEndpointResponse(
        id=endpoint.id,
        url=endpoint.url,
        secret=secret,
        events=endpoint.events,
        is_active=endpoint.is_active,
        created_at=endpoint.created_at,
    )


@router.get("/endpoints", response_model=List[WebhookEndpointResponse])
async def list_webhook_endpoints(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all webhook endpoints."""
    result = await db.execute(
        select(WebhookEndpoint).where(WebhookEndpoint.user_id == current_user.id)
    )
    return [
        WebhookEndpointResponse(
            id=e.id, url=e.url, secret=None, events=e.events,
            is_active=e.is_active, created_at=e.created_at,
        )
        for e in result.scalars().all()
    ]


@router.delete("/endpoints/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_endpoint(
    endpoint_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a webhook endpoint."""
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id,
            WebhookEndpoint.user_id == current_user.id,
        )
    )
    endpoint = result.scalar_one_or_none()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    endpoint.is_active = False
    await db.flush()


@router.get("/events", response_model=List[WebhookEventResponse])
async def list_webhook_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent webhook events."""
    result = await db.execute(
        select(WebhookEvent)
        .join(WebhookEndpoint)
        .where(WebhookEndpoint.user_id == current_user.id)
        .order_by(WebhookEvent.created_at.desc())
        .limit(50)
    )
    return [WebhookEventResponse.model_validate(e) for e in result.scalars().all()]


@router.get("/events/supported")
async def list_supported_events():
    """List all supported webhook event types."""
    return {"events": VALID_EVENTS}
