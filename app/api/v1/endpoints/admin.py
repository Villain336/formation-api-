"""Admin endpoints for managing orders, users, and system operations."""
from __future__ import annotations
from typing import List, Optional

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_admin_user
from app.db.session import get_db
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.models.ein import EINApplication, EINStatus
from app.models.registered_agent import RegisteredAgentService
from app.models.compliance import ComplianceTask, ComplianceStatus
from app.schemas.order import OrderResponse, OrderStatusUpdate
from app.services.order_service import get_order, update_order_status
from app.services.webhook_service import send_webhook

router = APIRouter()


@router.get("/dashboard")
async def admin_dashboard(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get admin dashboard metrics."""
    total_orders = (await db.execute(select(func.count()).select_from(Order))).scalar()
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar()

    status_counts = {}
    for s in OrderStatus:
        count = (await db.execute(
            select(func.count()).select_from(Order).where(Order.status == s)
        )).scalar()
        status_counts[s.value] = count

    total_revenue = (await db.execute(
        select(func.sum(Order.total_amount)).where(
            Order.status.in_([OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.FILED, OrderStatus.COMPLETED])
        )
    )).scalar() or 0

    return {
        "total_orders": total_orders,
        "total_users": total_users,
        "orders_by_status": status_counts,
        "total_revenue_cents": total_revenue,
        "total_revenue_usd": total_revenue / 100,
    }


@router.get("/orders", response_model=List[OrderResponse])
async def admin_list_orders(
    status: Optional[OrderStatus] = None,
    state: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all orders (admin view)."""
    query = (
        select(Order)
        .options(selectinload(Order.members))
        .order_by(Order.created_at.desc())
    )
    if status:
        query = query.where(Order.status == status)
    if state:
        query = query.where(Order.state_of_formation == state.upper())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return [OrderResponse.model_validate(o) for o in result.scalars().all()]


@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def admin_update_order_status(
    order_id: uuid.UUID,
    data: OrderStatusUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an order's status (admin action for processing orders)."""
    order = await get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        order = await update_order_status(
            db, order, data.status,
            changed_by=admin.id,
            notes=data.notes,
            state_filing_number=data.state_filing_number,
            rejection_reason=data.rejection_reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Send webhook notification
    await send_webhook(
        db,
        order.user_id,
        "order.status_changed",
        {
            "order_id": str(order.id),
            "order_number": order.order_number,
            "status": order.status.value,
            "business_name": order.business_name,
        },
    )

    return OrderResponse.model_validate(order)


@router.patch("/orders/{order_id}/ein")
async def admin_update_ein(
    order_id: uuid.UUID,
    ein_number: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Record EIN number for an order (after obtaining from IRS)."""
    result = await db.execute(
        select(EINApplication).where(EINApplication.order_id == order_id)
    )
    ein = result.scalar_one_or_none()
    if not ein:
        raise HTTPException(status_code=404, detail="EIN application not found")

    ein.ein_number = ein_number
    ein.status = EINStatus.RECEIVED
    ein.received_at = datetime.now(timezone.utc)
    await db.flush()

    # Send webhook
    order = await get_order(db, order_id)
    if order:
        await send_webhook(
            db, order.user_id, "ein.received",
            {"order_id": str(order_id), "ein_number": ein_number},
        )

    return {"status": "ok", "ein_number": ein_number}


@router.get("/users")
async def admin_list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users."""
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "company_name": u.company_name,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.get("/compliance/overdue")
async def admin_overdue_compliance(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all overdue compliance tasks."""
    result = await db.execute(
        select(ComplianceTask)
        .where(ComplianceTask.status.in_([ComplianceStatus.DUE, ComplianceStatus.OVERDUE]))
        .order_by(ComplianceTask.due_date)
    )
    tasks = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "order_id": str(t.order_id),
            "type": t.task_type.value,
            "status": t.status.value,
            "due_date": t.due_date.isoformat(),
            "state": t.state,
            "description": t.description,
        }
        for t in tasks
    ]
