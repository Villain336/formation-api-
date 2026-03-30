"""Stripe payment integration for formation orders."""

import uuid

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User

stripe.api_key = settings.STRIPE_SECRET_KEY


async def get_or_create_stripe_customer(db: AsyncSession, user: User) -> str:
    """Get or create a Stripe customer for the user."""
    if user.stripe_customer_id:
        return user.stripe_customer_id

    customer = stripe.Customer.create(
        email=user.email,
        name=user.full_name,
        metadata={"user_id": str(user.id)},
    )
    user.stripe_customer_id = customer.id
    await db.flush()
    return customer.id


async def create_payment_intent(db: AsyncSession, user: User, order: Order) -> dict:
    """Create a Stripe payment intent for an order."""
    if order.status not in (OrderStatus.DRAFT, OrderStatus.PENDING_PAYMENT):
        raise ValueError("Order is not in a payable state")

    if order.total_amount <= 0:
        raise ValueError("Order total must be greater than zero")

    customer_id = await get_or_create_stripe_customer(db, user)

    intent = stripe.PaymentIntent.create(
        amount=order.total_amount,
        currency="usd",
        customer=customer_id,
        metadata={
            "order_id": str(order.id),
            "order_number": order.order_number,
            "user_id": str(user.id),
        },
        description=f"Business formation: {order.business_name} ({order.entity_type.upper()}) in {order.state_of_formation}",
    )

    # Record payment
    payment = Payment(
        order_id=order.id,
        stripe_payment_intent_id=intent.id,
        amount=order.total_amount,
        currency="usd",
        status=PaymentStatus.PENDING,
        description=f"Formation of {order.business_name}",
    )
    db.add(payment)

    # Move order to pending payment
    if order.status == OrderStatus.DRAFT:
        order.status = OrderStatus.PENDING_PAYMENT

    await db.flush()

    return {
        "client_secret": intent.client_secret,
        "payment_intent_id": intent.id,
        "amount": order.total_amount,
        "currency": "usd",
    }


async def handle_payment_success(db: AsyncSession, payment_intent_id: str) -> Order | None:
    """Handle successful payment webhook from Stripe."""
    result = await db.execute(
        select(Payment).where(Payment.stripe_payment_intent_id == payment_intent_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        return None

    payment.status = PaymentStatus.SUCCEEDED

    result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = result.scalar_one_or_none()
    if order and order.status == OrderStatus.PENDING_PAYMENT:
        order.status = OrderStatus.PAID

    await db.flush()
    return order


async def handle_payment_failure(db: AsyncSession, payment_intent_id: str):
    """Handle failed payment webhook from Stripe."""
    result = await db.execute(
        select(Payment).where(Payment.stripe_payment_intent_id == payment_intent_id)
    )
    payment = result.scalar_one_or_none()
    if payment:
        payment.status = PaymentStatus.FAILED
        await db.flush()
