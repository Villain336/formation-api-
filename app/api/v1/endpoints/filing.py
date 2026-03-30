"""Filing management endpoints.

These endpoints expose the filing provider system:
- Users can check filing status for their orders
- Admins can manage the manual filing queue
- System can trigger filing submission for paid orders
"""
from __future__ import annotations
from typing import Optional, List, Dict

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.deps import get_current_user, get_admin_user
from app.db.session import get_db
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.models.filing import FilingSubmission, FilingStatusLog
from app.filing.router import filing_router

router = APIRouter()


# ============ Schemas ============

class FilingStatusResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    provider_name: str
    provider_type: str
    provider_reference_id: Optional[str]
    status: str
    status_message: Optional[str]
    state_filing_number: Optional[str]
    estimated_completion: Optional[str]
    is_expedited: bool
    attempt_number: int
    submitted_at: Optional[str]
    completed_at: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


class FilingProviderInfo(BaseModel):
    provider_name: str
    provider_type: str
    estimated_time_standard: str
    estimated_time_expedited: str
    is_direct: bool
    is_manual: bool


class AdminCompleteRequest(BaseModel):
    state_filing_number: str
    notes: Optional[str] = None


class AdminRejectRequest(BaseModel):
    rejection_reason: str
    notes: Optional[str] = None


# ============ User Endpoints ============

@router.get("/provider-info/{state}/{entity_type}", response_model=FilingProviderInfo)
async def get_filing_provider_info(state: str, entity_type: str):
    """Check which filing provider would handle a specific state/entity combo.

    Returns whether it's a direct state API integration or manual filing,
    plus estimated processing times.
    """
    try:
        info = filing_router.get_provider_info(state.upper(), entity_type)
        return FilingProviderInfo(**info)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/coverage")
async def get_filing_coverage():
    """Get the full filing coverage map.

    Shows which provider handles each state. States with direct API integration
    are marked as `direct: true`. States handled by manual queue are `direct: false`.
    """
    return {
        "coverage": filing_router.get_coverage(),
        "providers": filing_router.list_providers(),
        "direct_states": [
            s for s, info in filing_router.get_coverage().items() if info["direct"]
        ],
        "manual_states": [
            s for s, info in filing_router.get_coverage().items() if not info["direct"]
        ],
    }


@router.get("/orders/{order_id}/status")
async def get_order_filing_status(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the filing status for an order."""
    # Verify order belongs to user
    order_result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Get filing submissions
    result = await db.execute(
        select(FilingSubmission)
        .where(FilingSubmission.order_id == order_id)
        .order_by(FilingSubmission.created_at.desc())
    )
    submissions = result.scalars().all()

    return {
        "order_id": str(order_id),
        "order_status": order.status.value if hasattr(order.status, 'value') else order.status,
        "filings": [
            {
                "id": str(s.id),
                "provider": s.provider_name,
                "provider_type": s.provider_type,
                "status": s.status,
                "reference_id": s.provider_reference_id,
                "state_filing_number": s.state_filing_number,
                "estimated_completion": s.estimated_completion,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in submissions
        ],
    }


# ============ Admin Endpoints ============

@router.post("/submit/{order_id}", status_code=status.HTTP_201_CREATED)
async def submit_order_for_filing(
    order_id: uuid.UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Submit a paid order for filing.

    Automatically routes to the best available provider based on
    the order's state and entity type.
    """
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PAID:
        raise HTTPException(
            status_code=400,
            detail=f"Order must be in 'paid' status to file. Current: {order.status.value}",
        )

    submission = await filing_router.submit_filing(db, order)

    return {
        "submission_id": str(submission.id),
        "provider": submission.provider_name,
        "provider_type": submission.provider_type,
        "status": submission.status,
        "reference_id": submission.provider_reference_id,
        "estimated_completion": submission.estimated_completion,
        "message": submission.status_message,
    }


@router.post("/check/{submission_id}")
async def check_filing_submission_status(
    submission_id: uuid.UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Check and update the status of a filing submission."""
    try:
        submission = await filing_router.check_filing_status(db, submission_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "submission_id": str(submission.id),
        "status": submission.status,
        "state_filing_number": submission.state_filing_number,
        "message": submission.status_message,
    }


@router.post("/complete/{submission_id}")
async def admin_complete_filing(
    submission_id: uuid.UUID,
    data: AdminCompleteRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Mark a manual filing as complete.

    Used when an admin has manually filed through a state's website
    and received the state filing number.
    """
    try:
        submission = await filing_router.admin_complete_manual(
            db, submission_id, data.state_filing_number,
            admin_email=current_user.email, notes=data.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "submission_id": str(submission.id),
        "status": submission.status,
        "state_filing_number": submission.state_filing_number,
        "message": "Filing marked as complete. Order updated.",
    }


@router.get("/queue")
async def get_manual_queue(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Get all orders in the manual filing queue."""
    query = select(FilingSubmission).where(
        FilingSubmission.provider_type == "manual"
    ).order_by(FilingSubmission.created_at.asc())

    if status_filter:
        query = query.where(FilingSubmission.status == status_filter)

    result = await db.execute(query)
    submissions = result.scalars().all()

    return {
        "total": len(submissions),
        "queue": [
            {
                "id": str(s.id),
                "order_id": str(s.order_id),
                "status": s.status,
                "is_expedited": s.is_expedited,
                "estimated_completion": s.estimated_completion,
                "admin_notes": s.admin_notes,
                "assigned_to": s.assigned_to,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in submissions
        ],
    }


@router.get("/history/{submission_id}")
async def get_filing_status_history(
    submission_id: uuid.UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """[Admin] Get the full status audit trail for a filing submission."""
    result = await db.execute(
        select(FilingStatusLog)
        .where(FilingStatusLog.submission_id == submission_id)
        .order_by(FilingStatusLog.created_at.asc())
    )
    logs = result.scalars().all()

    return {
        "submission_id": str(submission_id),
        "history": [
            {
                "from_status": l.from_status,
                "to_status": l.to_status,
                "message": l.message,
                "changed_by": l.changed_by,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
    }
