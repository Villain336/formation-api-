"""Payment endpoints: Stripe integration for order payments."""

import uuid

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import CreatePaymentIntent, PaymentIntentResponse
from app.services.order_service import get_order
from app.services.payment_service import (
    create_payment_intent,
    handle_payment_success,
    handle_payment_failure,
)

router = APIRouter()


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_intent(
    data: CreatePaymentIntent,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe PaymentIntent for an order."""
    order = await get_order(db, data.order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        result = await create_payment_intent(db, current_user, order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.StripeError as e:
        raise HTTPException(status_code=502, detail=f"Payment provider error: {str(e)}")

    return PaymentIntentResponse(**result)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        await handle_payment_success(db, pi["id"])

    elif event["type"] == "payment_intent.payment_failed":
        pi = event["data"]["object"]
        await handle_payment_failure(db, pi["id"])

    return {"status": "ok"}
