"""Webhook delivery service for notifying clients of events."""

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import WebhookEndpoint, WebhookEvent


async def send_webhook(
    db: AsyncSession,
    user_id: uuid.UUID,
    event_type: str,
    payload: dict,
):
    """Send webhook to all active endpoints for a user that subscribe to this event type."""
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.user_id == user_id,
            WebhookEndpoint.is_active.is_(True),
        )
    )
    endpoints = result.scalars().all()

    for endpoint in endpoints:
        if event_type not in endpoint.events:
            continue

        event = WebhookEvent(
            endpoint_id=endpoint.id,
            event_type=event_type,
            payload=payload,
        )
        db.add(event)
        await db.flush()

        # Attempt delivery
        try:
            body = json.dumps(payload, default=str)
            signature = hmac.new(
                endpoint.secret.encode(), body.encode(), hashlib.sha256
            ).hexdigest()

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    endpoint.url,
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": signature,
                        "X-Webhook-Event": event_type,
                        "X-Webhook-ID": str(event.id),
                    },
                )
                event.status_code = response.status_code
                event.attempts = 1
                if 200 <= response.status_code < 300:
                    event.delivered_at = datetime.now(timezone.utc)
                event.last_attempt_at = datetime.now(timezone.utc)
        except Exception:
            event.attempts = 1
            event.last_attempt_at = datetime.now(timezone.utc)

        await db.flush()
