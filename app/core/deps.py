from __future__ import annotations
from typing import Optional

import uuid
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_token, verify_password
from app.db.session import get_db
from app.models.user import User, APIKey

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    api_key: Optional[str] = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate via JWT bearer token or API key."""
    # Try JWT first
    if credentials:
        user_id = verify_token(credentials.credentials)
        if user_id:
            result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
            user = result.scalar_one_or_none()
            if user and user.is_active:
                return user

    # Try API key
    if api_key:
        from app.core.security import verify_password as _verify

        result = await db.execute(select(APIKey).where(APIKey.is_active.is_(True)))
        keys = result.scalars().all()
        for key in keys:
            if _verify(api_key, key.key_hash):
                key.last_used_at = datetime.now(timezone.utc)
                user_result = await db.execute(select(User).where(User.id == key.user_id))
                user = user_result.scalar_one_or_none()
                if user and user.is_active:
                    return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
