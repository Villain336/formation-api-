"""Filing Provider Interface.

This module defines the abstract interface that all filing providers must implement.
Providers can be:
- Direct state API integrations (Delaware, Texas, Florida, Wyoming, etc.)
- Wholesale vendors (NRAI, CSC, CT Corporation)
- Manual filing queue (fallback for any state)

The FilingRouter automatically selects the best provider for each order based on
state, entity type, and provider availability.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict


class FilingStatus(str, Enum):
    """Status of a filing submission."""
    QUEUED = "queued"                # Accepted, waiting to be submitted
    SUBMITTING = "submitting"        # Being submitted to state/vendor
    SUBMITTED = "submitted"          # Submitted, awaiting state response
    PENDING_REVIEW = "pending_review"  # State is reviewing
    APPROVED = "approved"            # State approved, entity formed
    REJECTED = "rejected"            # State rejected, needs correction
    FAILED = "failed"                # System error, needs retry
    CANCELLED = "cancelled"


class ProviderType(str, Enum):
    """Type of filing provider."""
    STATE_DIRECT = "state_direct"    # Direct state API/portal
    VENDOR = "vendor"                # Wholesale vendor (NRAI, CSC)
    MANUAL = "manual"                # Manual filing queue


@dataclass
class FilingRequest:
    """Data sent to a filing provider."""
    order_id: uuid.UUID
    entity_type: str               # llc, corporation, etc.
    state: str                     # Two-letter state code
    business_name: str
    business_name_alt1: Optional[str] = None
    business_name_alt2: Optional[str] = None
    business_purpose: Optional[str] = None
    address_line1: str = ""
    address_line2: Optional[str] = None
    city: str = ""
    state_code: str = ""
    zip_code: str = ""
    members: List[Dict] = field(default_factory=list)
    registered_agent_name: Optional[str] = None
    registered_agent_address: Optional[str] = None
    expedited: bool = False
    metadata: Dict = field(default_factory=dict)


@dataclass
class FilingResult:
    """Result returned from a filing provider."""
    status: FilingStatus
    provider_name: str
    provider_type: ProviderType
    provider_reference_id: Optional[str] = None   # Provider's tracking ID
    state_filing_number: Optional[str] = None      # Official state filing number
    formation_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    documents: List[Dict] = field(default_factory=list)  # [{filename, url, doc_type}]
    estimated_completion: Optional[str] = None     # "2-3 business days"
    raw_response: Optional[Dict] = None            # Full provider response for debugging
    message: str = ""


class FilingProvider(ABC):
    """Abstract base class for all filing providers.

    Every provider must implement these methods. The FilingRouter
    calls them in this order:
    1. supports(state, entity_type) — can this provider handle this order?
    2. get_estimated_time(state, entity_type, expedited) — how long?
    3. submit(request) — submit the filing
    4. check_status(reference_id) — poll for updates
    5. cancel(reference_id) — cancel if possible
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Type of provider."""

    @abstractmethod
    def supports(self, state: str, entity_type: str) -> bool:
        """Check if this provider can handle the given state and entity type."""

    @abstractmethod
    async def submit(self, request: FilingRequest) -> FilingResult:
        """Submit a filing request. Returns initial result with tracking info."""

    @abstractmethod
    async def check_status(self, provider_reference_id: str) -> FilingResult:
        """Check the current status of a submitted filing."""

    @abstractmethod
    async def cancel(self, provider_reference_id: str) -> bool:
        """Attempt to cancel a filing. Returns True if successful."""

    def get_estimated_time(self, state: str, entity_type: str, expedited: bool = False) -> str:
        """Return estimated processing time as a human-readable string."""
        return "5-10 business days"

    def get_priority(self, state: str, entity_type: str) -> int:
        """Return priority (lower = preferred). Used by router to pick best provider."""
        return 100
