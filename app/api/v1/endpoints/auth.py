"""Authentication endpoints: register, login, API key management."""
from __future__ import annotations
from typing import List

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password, create_access_token, generate_api_key
from app.db.session import get_db
from app.models.user import User, APIKey
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    TokenResponse, APIKeyCreate, APIKeyResponse, APIKeyRenew, APIKeyUpdate,
    AVAILABLE_SCOPES,
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone,
        company_name=data.company_name,
    )
    db.add(user)
    await db.flush()

    token = create_access_token(str(user.id))
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(str(user.id))
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    await db.flush()
    return UserResponse.model_validate(current_user)


@router.get("/scopes")
async def list_available_scopes():
    """List all available API key scopes."""
    return {"scopes": AVAILABLE_SCOPES}


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: APIKeyCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key.

    The full key is only returned once at creation time. Store it securely.
    Keys use the format: form_test_... (test) or form_live_... (live).
    """
    # Validate environment
    if data.environment not in ("test", "live"):
        raise HTTPException(status_code=400, detail="Environment must be 'test' or 'live'")

    # Validate scopes
    invalid_scopes = set(data.scopes) - set(AVAILABLE_SCOPES.keys())
    if invalid_scopes:
        raise HTTPException(status_code=400, detail=f"Invalid scopes: {invalid_scopes}")

    # Check key limits per plan
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == current_user.id, APIKey.is_active.is_(True))
    )
    active_keys = len(result.scalars().all())
    plan_limits = {"free": 2, "starter": 10, "growth": 50, "enterprise": 200}
    limit = plan_limits.get(current_user.plan, 2)
    if active_keys >= limit:
        raise HTTPException(
            status_code=400,
            detail=f"API key limit reached ({limit}). Upgrade your plan for more keys.",
        )

    raw_key = generate_api_key()
    # Add environment prefix
    env_key = raw_key.replace("form_", f"form_{data.environment}_", 1)
    key_prefix = env_key[:16]

    expires_at = None
    if data.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_in_days)

    api_key = APIKey(
        user_id=current_user.id,
        key_hash=hash_password(env_key),
        key_prefix=key_prefix,
        name=data.name,
        description=data.description,
        environment=data.environment,
        scopes=data.scopes if data.scopes else list(AVAILABLE_SCOPES.keys()),
        rate_limit_per_minute=data.rate_limit_per_minute,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.flush()

    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        key=env_key,  # Only returned once!
        key_prefix=key_prefix,
        environment=api_key.environment,
        scopes=api_key.scopes or [],
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        rate_limit_per_day=api_key.rate_limit_per_day,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        total_requests=api_key.total_requests,
        created_at=api_key.created_at,
    )


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for the current user. Key values are never shown after creation."""
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == current_user.id).order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        APIKeyResponse(
            id=k.id, name=k.name, description=k.description, key=None,
            key_prefix=k.key_prefix, environment=k.environment,
            scopes=k.scopes or [], rate_limit_per_minute=k.rate_limit_per_minute,
            rate_limit_per_day=k.rate_limit_per_day, is_active=k.is_active,
            expires_at=k.expires_at, last_used_at=k.last_used_at,
            last_used_ip=k.last_used_ip, total_requests=k.total_requests,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.patch("/api-keys/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: uuid.UUID,
    data: APIKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an API key's name, scopes, or rate limits."""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    update_data = data.model_dump(exclude_unset=True)
    if "scopes" in update_data:
        invalid = set(update_data["scopes"]) - set(AVAILABLE_SCOPES.keys())
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid scopes: {invalid}")

    for field, value in update_data.items():
        setattr(key, field, value)
    await db.flush()

    return APIKeyResponse(
        id=key.id, name=key.name, description=key.description, key=None,
        key_prefix=key.key_prefix, environment=key.environment,
        scopes=key.scopes or [], rate_limit_per_minute=key.rate_limit_per_minute,
        rate_limit_per_day=key.rate_limit_per_day, is_active=key.is_active,
        expires_at=key.expires_at, last_used_at=key.last_used_at,
        last_used_ip=key.last_used_ip, total_requests=key.total_requests,
        created_at=key.created_at,
    )


@router.post("/api-keys/{key_id}/renew", response_model=APIKeyResponse)
async def renew_api_key(
    key_id: uuid.UUID,
    data: APIKeyRenew,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Renew an API key by extending its expiration date."""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    key.expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_in_days)
    key.is_active = True
    await db.flush()

    return APIKeyResponse(
        id=key.id, name=key.name, description=key.description, key=None,
        key_prefix=key.key_prefix, environment=key.environment,
        scopes=key.scopes or [], rate_limit_per_minute=key.rate_limit_per_minute,
        rate_limit_per_day=key.rate_limit_per_day, is_active=key.is_active,
        expires_at=key.expires_at, last_used_at=key.last_used_at,
        last_used_ip=key.last_used_ip, total_requests=key.total_requests,
        created_at=key.created_at,
    )


@router.post("/api-keys/{key_id}/roll", response_model=APIKeyResponse)
async def roll_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Roll (rotate) an API key. Deactivates the old key and creates a new one with same settings."""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    old_key = result.scalar_one_or_none()
    if not old_key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Deactivate old key
    old_key.is_active = False

    # Create new key with same settings
    raw_key = generate_api_key()
    env_key = raw_key.replace("form_", f"form_{old_key.environment}_", 1)

    new_key = APIKey(
        user_id=current_user.id,
        key_hash=hash_password(env_key),
        key_prefix=env_key[:16],
        name=old_key.name,
        description=old_key.description,
        environment=old_key.environment,
        scopes=old_key.scopes,
        rate_limit_per_minute=old_key.rate_limit_per_minute,
        rate_limit_per_day=old_key.rate_limit_per_day,
        expires_at=old_key.expires_at,
    )
    db.add(new_key)
    await db.flush()

    return APIKeyResponse(
        id=new_key.id, name=new_key.name, description=new_key.description,
        key=env_key,  # New key returned once
        key_prefix=new_key.key_prefix, environment=new_key.environment,
        scopes=new_key.scopes or [], rate_limit_per_minute=new_key.rate_limit_per_minute,
        rate_limit_per_day=new_key.rate_limit_per_day, is_active=new_key.is_active,
        expires_at=new_key.expires_at, last_used_at=None,
        total_requests=0, created_at=new_key.created_at,
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently deactivate an API key. This action cannot be undone."""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.is_active = False
    await db.flush()
