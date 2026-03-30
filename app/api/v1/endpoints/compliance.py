"""Compliance tracking endpoints."""
from __future__ import annotations
from typing import Optional, List

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.compliance import ComplianceTask, ComplianceStatus
from app.models.order import Order
from app.models.user import User
from app.schemas.compliance import ComplianceTaskResponse, ComplianceTaskUpdate

router = APIRouter()


@router.get("/tasks", response_model=list[ComplianceTaskResponse])
async def list_compliance_tasks(
    status: Optional[ComplianceStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all compliance tasks for the current user's orders."""
    query = (
        select(ComplianceTask)
        .join(Order)
        .where(Order.user_id == current_user.id)
        .order_by(ComplianceTask.due_date)
    )
    if status:
        query = query.where(ComplianceTask.status == status)

    result = await db.execute(query)
    return [ComplianceTaskResponse.model_validate(t) for t in result.scalars().all()]


@router.get("/tasks/{task_id}", response_model=ComplianceTaskResponse)
async def get_compliance_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific compliance task."""
    result = await db.execute(
        select(ComplianceTask)
        .join(Order)
        .where(ComplianceTask.id == task_id, Order.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Compliance task not found")
    return ComplianceTaskResponse.model_validate(task)


@router.patch("/tasks/{task_id}", response_model=ComplianceTaskResponse)
async def update_compliance_task(
    task_id: uuid.UUID,
    data: ComplianceTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a compliance task status."""
    result = await db.execute(
        select(ComplianceTask)
        .join(Order)
        .where(ComplianceTask.id == task_id, Order.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Compliance task not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    await db.flush()

    return ComplianceTaskResponse.model_validate(task)
