"""State requirements and entity type endpoints."""
from __future__ import annotations
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.entity import EntityType, StateRequirement
from app.schemas.entity import EntityTypeResponse, StateRequirementResponse, StateListResponse

router = APIRouter()


@router.get("/entity-types", response_model=list[EntityTypeResponse])
async def list_entity_types(db: AsyncSession = Depends(get_db)):
    """List all supported entity types."""
    result = await db.execute(select(EntityType).where(EntityType.is_active.is_(True)))
    return [EntityTypeResponse.model_validate(et) for et in result.scalars().all()]


@router.get("/requirements", response_model=StateListResponse)
async def list_state_requirements(
    entity_type: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List state formation requirements. Filter by entity type and/or state."""
    query = select(StateRequirement)
    if entity_type:
        query = query.where(StateRequirement.entity_type == entity_type)
    if state:
        query = query.where(StateRequirement.state_code == state.upper())
    query = query.order_by(StateRequirement.state_name)

    result = await db.execute(query)
    states = result.scalars().all()
    return StateListResponse(
        states=[StateRequirementResponse.model_validate(s) for s in states],
        total=len(states),
    )


@router.get("/requirements/{state_code}/{entity_type}", response_model=StateRequirementResponse)
async def get_state_requirement(
    state_code: str,
    entity_type: str,
    db: AsyncSession = Depends(get_db),
):
    """Get specific state requirements for an entity type."""
    result = await db.execute(
        select(StateRequirement).where(
            StateRequirement.state_code == state_code.upper(),
            StateRequirement.entity_type == entity_type,
        )
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(
            status_code=404,
            detail=f"No requirements found for {entity_type} in {state_code.upper()}",
        )
    return StateRequirementResponse.model_validate(req)


@router.get("/available-states", response_model=list[str])
async def list_available_states(
    entity_type: str = Query(default="llc"),
    db: AsyncSession = Depends(get_db),
):
    """List all states where a specific entity type can be formed."""
    result = await db.execute(
        select(distinct(StateRequirement.state_code))
        .where(StateRequirement.entity_type == entity_type)
        .order_by(StateRequirement.state_code)
    )
    return [row[0] for row in result.all()]
