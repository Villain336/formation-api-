import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None
    company_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    company_name: str | None
    is_active: bool
    plan: str = "free"
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    company_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class APIKeyCreate(BaseModel):
    name: str
    description: str | None = None
    environment: str = "test"  # test or live
    scopes: list[str] = []  # ["orders:read", "orders:write", "states:read"]
    rate_limit_per_minute: int = 60
    expires_in_days: int | None = None  # None = no expiry


class APIKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    key: str | None = None  # Only returned on creation
    key_prefix: str
    environment: str
    scopes: list[str]
    rate_limit_per_minute: int
    rate_limit_per_day: int
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    last_used_ip: str | None = None
    total_requests: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyRenew(BaseModel):
    expires_in_days: int = 365


class APIKeyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    scopes: list[str] | None = None
    rate_limit_per_minute: int | None = None
    is_active: bool | None = None


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
