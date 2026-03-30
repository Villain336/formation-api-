from __future__ import annotations
from typing import Optional, List

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    company_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone: Optional[str]
    company_name: Optional[str]
    is_active: bool
    plan: str = "free"
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class APIKeyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    environment: str = "test"  # test or live
    scopes: list[str] = []  # ["orders:read", "orders:write", "states:read"]
    rate_limit_per_minute: int = 60
    expires_in_days: Optional[int] = None  # None = no expiry


class APIKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    key: Optional[str] = None  # Only returned on creation
    key_prefix: str
    environment: str
    scopes: list[str]
    rate_limit_per_minute: int
    rate_limit_per_day: int
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    last_used_ip: Optional[str] = None
    total_requests: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyRenew(BaseModel):
    expires_in_days: int = 365


class APIKeyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    rate_limit_per_minute: Optional[int] = None
    is_active: Optional[bool] = None


# Available scopes for documentation
AVAILABLE_SCOPES = {
    "orders:read": "Read formation orders",
    "orders:write": "Create and update formation orders",
    "orders:delete": "Cancel formation orders",
    "states:read": "Read state requirements and fees",
    "documents:read": "Download generated documents",
    "payments:read": "View payment history",
    "payments:write": "Create payment intents",
    "webhooks:read": "View webhook configurations",
    "webhooks:write": "Create and manage webhooks",
    "compliance:read": "View compliance tasks",
    "ein:read": "View EIN applications",
    "keys:read": "View API key metadata",
    "keys:write": "Create and manage API keys",
}
