"""Order management endpoints: create, read, update, name check, pricing."""
from __future__ import annotations
from typing import Optional, List

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.order import Order, OrderStatus
from app.models.entity import StateRequirement
from app.models.user import User
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse,
    PricingResponse, NameCheckRequest, NameCheckResponse,
)
from app.schemas.member import MemberCreate, MemberResponse
from app.models.member import Member
from app.services.order_service import create_order, get_order, list_orders, update_order
from app.services.pricing import calculate_pricing

router = APIRouter()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_formation_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new business formation order."""
    # Validate entity type and state
    result = await db.execute(
        select(StateRequirement).where(
            StateRequirement.state_code == data.state_of_formation.upper(),
            StateRequirement.entity_type == data.entity_type,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Formation of {data.entity_type} is not available in {data.state_of_formation}",
        )

    order = await create_order(db, current_user.id, data)
    return OrderResponse.model_validate(order)


@router.get("", response_model=OrderListResponse)
async def list_formation_orders(
    status: Optional[OrderStatus] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all formation orders for the current user."""
    orders, total = await list_orders(db, current_user.id, status, page, per_page)
    return OrderListResponse(
        orders=[OrderResponse.model_validate(o) for o in orders],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_formation_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific formation order."""
    order = await get_order(db, order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse.model_validate(order)


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_formation_order(
    order_id: uuid.UUID,
    data: OrderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a draft formation order."""
    order = await get_order(db, order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        order = await update_order(db, order, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return OrderResponse.model_validate(order)


@router.post("/{order_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    order_id: uuid.UUID,
    data: MemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a member/officer to a formation order."""
    order = await get_order(db, order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only add members to draft orders")

    member = Member(order_id=order.id, **data.model_dump())
    db.add(member)
    await db.flush()
    return MemberResponse.model_validate(member)


@router.delete("/{order_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    order_id: uuid.UUID,
    member_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from a formation order."""
    order = await get_order(db, order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only modify draft orders")

    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.order_id == order.id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    await db.delete(member)


@router.post("/pricing", response_model=PricingResponse)
async def get_pricing(
    entity_type: str,
    state: str,
    processing_speed: str = "standard",
    include_registered_agent: bool = True,
    include_ein: bool = False,
    include_operating_agreement: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Get pricing estimate for a formation order (no auth required)."""
    from app.models.order import ProcessingSpeed as PS

    try:
        speed = PS(processing_speed)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid processing speed")

    pricing = await calculate_pricing(
        db, entity_type, state.upper(), speed,
        include_registered_agent, include_ein, include_operating_agreement,
    )
    return PricingResponse(**pricing)


@router.post("/name-check", response_model=NameCheckResponse)
async def check_name_availability(
    data: NameCheckRequest,
    db: AsyncSession = Depends(get_db),
):
    """Check business name availability and get naming rules.

    Note: This performs a basic check against naming rules.
    For definitive availability, check with the state's Secretary of State.
    """
    result = await db.execute(
        select(StateRequirement).where(
            StateRequirement.state_code == data.state.upper(),
            StateRequirement.entity_type == data.entity_type,
        )
    )
    state_req = result.scalar_one_or_none()

    naming_rules = state_req.naming_rules if state_req else None

    # Check if name has required suffix
    has_valid_suffix = True
    if naming_rules and "required_suffix" in naming_rules:
        suffixes = naming_rules["required_suffix"]
        has_valid_suffix = any(data.business_name.upper().endswith(s.upper()) for s in suffixes)

    # Check for restricted words
    has_restricted = False
    if naming_rules and "restricted_words" in naming_rules:
        name_lower = data.business_name.lower()
        has_restricted = any(word in name_lower for word in naming_rules["restricted_words"])

    available = has_valid_suffix and not has_restricted

    suggestions = []
    if not has_valid_suffix and naming_rules and "required_suffix" in naming_rules:
        base = data.business_name.strip()
        for suffix in naming_rules["required_suffix"][:3]:
            suggestions.append(f"{base} {suffix}")

    return NameCheckResponse(
        available=available,
        business_name=data.business_name,
        state=data.state.upper(),
        suggestions=suggestions,
        naming_rules=naming_rules,
    )
