"""Order creation and management service."""
from __future__ import annotations
from typing import Optional, List

import uuid
from datetime import datetime, date, timezone
from dateutil.relativedelta import relativedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderStatus, OrderStatusHistory
from app.models.member import Member
from app.models.registered_agent import RegisteredAgentService, RAStatus
from app.models.ein import EINApplication
from app.models.compliance import ComplianceTask, ComplianceType, ComplianceStatus
from app.models.entity import StateRequirement
from app.schemas.order import OrderCreate, OrderUpdate
from app.services.pricing import calculate_pricing
from app.utils.order_number import generate_order_number


async def create_order(db: AsyncSession, user_id: uuid.UUID, data: OrderCreate) -> Order:
    """Create a new formation order with pricing calculation."""
    pricing = await calculate_pricing(
        db=db,
        entity_type=data.entity_type,
        state_code=data.state_of_formation,
        processing_speed=data.processing_speed,
        include_registered_agent=data.include_registered_agent,
        include_ein=data.include_ein,
        include_operating_agreement=data.include_operating_agreement,
    )

    order = Order(
        user_id=user_id,
        order_number=generate_order_number(),
        status=OrderStatus.DRAFT,
        entity_type=data.entity_type,
        state_of_formation=data.state_of_formation.upper(),
        business_name=data.business_name,
        business_name_alt1=data.business_name_alt1,
        business_name_alt2=data.business_name_alt2,
        business_purpose=data.business_purpose,
        business_address_line1=data.business_address_line1,
        business_address_line2=data.business_address_line2,
        business_city=data.business_city,
        business_state=data.business_state.upper(),
        business_zip=data.business_zip,
        processing_speed=data.processing_speed,
        include_registered_agent=data.include_registered_agent,
        include_ein=data.include_ein,
        include_operating_agreement=data.include_operating_agreement,
        state_fee=pricing["state_fee"],
        service_fee=pricing["service_fee"],
        expedited_fee=pricing["expedited_fee"],
        registered_agent_fee=pricing["registered_agent_fee"],
        total_amount=pricing["total_amount"],
    )
    db.add(order)
    await db.flush()

    # Add members
    for member_data in data.members:
        member = Member(order_id=order.id, **member_data.model_dump())
        db.add(member)

    # Record status history
    db.add(OrderStatusHistory(
        order_id=order.id,
        from_status=None,
        to_status=OrderStatus.DRAFT.value,
        notes="Order created",
    ))

    await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.members), selectinload(Order.documents))
        .where(Order.id == order.id)
    )
    return result.scalar_one()


async def get_order(db: AsyncSession, order_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Optional[Order]:
    """Get order by ID, optionally filtered by user."""
    query = (
        select(Order)
        .options(selectinload(Order.members), selectinload(Order.documents))
        .where(Order.id == order_id)
    )
    if user_id:
        query = query.where(Order.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_orders(
    db: AsyncSession,
    user_id: uuid.UUID,
    status: Optional[OrderStatus] = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Order], int]:
    """List orders for a user with pagination."""
    query = (
        select(Order)
        .options(selectinload(Order.members))
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
    )
    if status:
        query = query.where(Order.status == status)

    # Count
    count_query = select(func.count()).select_from(Order).where(Order.user_id == user_id)
    if status:
        count_query = count_query.where(Order.status == status)
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all(), total


async def update_order(db: AsyncSession, order: Order, data: OrderUpdate) -> Order:
    """Update a draft order."""
    if order.status != OrderStatus.DRAFT:
        raise ValueError("Can only update orders in draft status")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    # Recalculate pricing if relevant fields changed
    pricing_fields = {"processing_speed", "include_registered_agent", "include_ein", "include_operating_agreement"}
    if pricing_fields & set(update_data.keys()):
        pricing = await calculate_pricing(
            db=db,
            entity_type=order.entity_type,
            state_code=order.state_of_formation,
            processing_speed=order.processing_speed,
            include_registered_agent=order.include_registered_agent,
            include_ein=order.include_ein,
            include_operating_agreement=order.include_operating_agreement,
        )
        order.state_fee = pricing["state_fee"]
        order.service_fee = pricing["service_fee"]
        order.expedited_fee = pricing["expedited_fee"]
        order.registered_agent_fee = pricing["registered_agent_fee"]
        order.total_amount = pricing["total_amount"]

    await db.flush()
    return order


async def update_order_status(
    db: AsyncSession,
    order: Order,
    new_status: OrderStatus,
    changed_by: Optional[uuid.UUID] = None,
    notes: Optional[str] = None,
    state_filing_number: Optional[str] = None,
    rejection_reason: Optional[str] = None,
) -> Order:
    """Transition order to a new status with validation."""
    valid_transitions = {
        OrderStatus.DRAFT: [OrderStatus.PENDING_PAYMENT, OrderStatus.CANCELLED],
        OrderStatus.PENDING_PAYMENT: [OrderStatus.PAID, OrderStatus.CANCELLED],
        OrderStatus.PAID: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
        OrderStatus.PROCESSING: [OrderStatus.FILED, OrderStatus.REJECTED, OrderStatus.CANCELLED],
        OrderStatus.FILED: [OrderStatus.COMPLETED],
        OrderStatus.REJECTED: [OrderStatus.PROCESSING],  # Can retry
    }

    allowed = valid_transitions.get(order.status, [])
    if new_status not in allowed:
        raise ValueError(f"Cannot transition from {order.status.value} to {new_status.value}")

    old_status = order.status
    order.status = new_status

    if state_filing_number:
        order.state_filing_number = state_filing_number
    if rejection_reason:
        order.rejection_reason = rejection_reason
    if new_status == OrderStatus.FILED:
        order.filed_at = datetime.now(timezone.utc)
    if new_status == OrderStatus.COMPLETED:
        order.effective_date = datetime.now(timezone.utc)
        # Create compliance tasks on completion
        await _create_compliance_tasks(db, order)
        # Activate registered agent if included
        if order.include_registered_agent:
            await _activate_registered_agent(db, order)

    db.add(OrderStatusHistory(
        order_id=order.id,
        from_status=old_status.value,
        to_status=new_status.value,
        changed_by=changed_by,
        notes=notes,
    ))

    await db.flush()
    return order


async def _create_compliance_tasks(db: AsyncSession, order: Order):
    """Create compliance tasks when an order is completed."""
    result = await db.execute(
        select(StateRequirement).where(
            StateRequirement.state_code == order.state_of_formation,
            StateRequirement.entity_type == order.entity_type,
        )
    )
    state_req = result.scalar_one_or_none()
    if not state_req:
        return

    now = datetime.now(timezone.utc)
    next_year = now + relativedelta(years=1)

    # Annual report
    if state_req.annual_report_fee and state_req.annual_report_fee > 0:
        month = state_req.annual_report_month or now.month
        due = date(next_year.year, month, 1)
        db.add(ComplianceTask(
            order_id=order.id,
            task_type=ComplianceType.ANNUAL_REPORT,
            status=ComplianceStatus.UPCOMING,
            due_date=due,
            state=order.state_of_formation,
            description=f"Annual report due for {order.business_name} in {state_req.state_name}",
        ))

    # Franchise tax (DE, CA, etc.)
    if state_req.franchise_tax and state_req.franchise_tax > 0:
        due = date(next_year.year, 3, 1)  # Most are due in March
        db.add(ComplianceTask(
            order_id=order.id,
            task_type=ComplianceType.FRANCHISE_TAX,
            status=ComplianceStatus.UPCOMING,
            due_date=due,
            state=order.state_of_formation,
            description=f"Franchise tax due for {order.business_name} in {state_req.state_name}",
        ))

    # Publication requirement (NY, AZ, NE, PA)
    if state_req.requires_publication:
        due = date(now.year, now.month, now.day) + relativedelta(days=120)
        db.add(ComplianceTask(
            order_id=order.id,
            task_type=ComplianceType.PUBLICATION,
            status=ComplianceStatus.DUE,
            due_date=due,
            state=order.state_of_formation,
            description=f"Publication requirement for {order.business_name} in {state_req.state_name}. Must publish in two newspapers.",
        ))

    # BOI Report (federal requirement)
    db.add(ComplianceTask(
        order_id=order.id,
        task_type=ComplianceType.BOI_REPORT,
        status=ComplianceStatus.DUE,
        due_date=date(now.year, now.month, now.day) + relativedelta(days=90),
        state=order.state_of_formation,
        description=f"Beneficial Ownership Information (BOI) report due to FinCEN for {order.business_name}",
    ))


async def _activate_registered_agent(db: AsyncSession, order: Order):
    """Create/activate registered agent service for completed order."""
    today = date.today()
    renewal = today + relativedelta(years=1)
    db.add(RegisteredAgentService(
        order_id=order.id,
        state=order.state_of_formation,
        status=RAStatus.ACTIVE,
        start_date=today,
        renewal_date=renewal,
        annual_fee=order.registered_agent_fee,
        auto_renew=True,
    ))
