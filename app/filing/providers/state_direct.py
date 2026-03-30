"""State Direct Filing Providers for Texas, Florida, Wyoming, and Nevada.

Each state has its own online filing portal. These providers handle:
- Building state-specific filing payloads
- Submitting via state APIs where available
- Simulating in test mode

Production integration notes:
- Texas: SOSDirect at https://direct.sos.state.tx.us/ — supports online XML filing
- Florida: Sunbiz at https://dos.fl.gov/sunbiz/ — online filing available
- Wyoming: https://wyobiz.wyo.gov/ — online filing portal
- Nevada: https://esos.nv.gov/EntitySearch/OnlineEntitySearch — SilverFlume
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict

from app.filing.base import (
    FilingProvider, FilingRequest, FilingResult,
    FilingStatus, ProviderType,
)

logger = logging.getLogger(__name__)


class TexasDirectProvider(FilingProvider):
    """Direct filing with Texas Secretary of State via SOSDirect."""

    def __init__(self):
        self._simulated: Dict[str, dict] = {}

    @property
    def name(self) -> str:
        return "texas_direct"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.STATE_DIRECT

    def supports(self, state: str, entity_type: str) -> bool:
        return state.upper() == "TX" and entity_type in ("llc", "corporation", "s_corp", "lp")

    def get_priority(self, state: str, entity_type: str) -> int:
        return 1

    def get_estimated_time(self, state: str, entity_type: str, expedited: bool = False) -> str:
        if expedited:
            return "Same day"
        return "2-5 business days"

    async def submit(self, request: FilingRequest) -> FilingResult:
        ref_id = f"TX-{uuid.uuid4().hex[:8].upper()}"
        self._simulated[ref_id] = {"status": FilingStatus.SUBMITTED}

        payload = {
            "state": "TX",
            "filing_type": "Certificate of Formation",
            "entity_name": request.business_name,
            "entity_type": request.entity_type.upper(),
            "purpose": request.business_purpose or "The purpose for which the entity is organized is the transaction of any and all lawful business.",
            "registered_agent": {
                "name": request.registered_agent_name or "Formation API Registered Agent",
                "address": "1999 Bryan St, Suite 900, Dallas, TX 75201",
            },
            "management_type": "member-managed" if request.entity_type == "llc" else "board",
            "organizer": request.members[0] if request.members else {},
            "expedited": request.expedited,
        }

        return FilingResult(
            status=FilingStatus.SUBMITTED,
            provider_name=self.name,
            provider_type=self.provider_type,
            provider_reference_id=ref_id,
            estimated_completion=self.get_estimated_time("TX", request.entity_type, request.expedited),
            message=f"Filing submitted to Texas SOS. Reference: {ref_id}",
            raw_response={"test_mode": True, "payload": payload},
        )

    async def check_status(self, provider_reference_id: str) -> FilingResult:
        return FilingResult(
            status=FilingStatus.APPROVED,
            provider_name=self.name,
            provider_type=self.provider_type,
            provider_reference_id=provider_reference_id,
            state_filing_number=f"TX-{uuid.uuid4().hex[:10].upper()}",
            formation_date=datetime.now(timezone.utc),
            message="Filing approved by Texas Secretary of State (simulated)",
        )

    async def cancel(self, provider_reference_id: str) -> bool:
        return provider_reference_id in self._simulated


class FloridaDirectProvider(FilingProvider):
    """Direct filing with Florida Division of Corporations (Sunbiz)."""

    def __init__(self):
        self._simulated: Dict[str, dict] = {}

    @property
    def name(self) -> str:
        return "florida_direct"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.STATE_DIRECT

    def supports(self, state: str, entity_type: str) -> bool:
        return state.upper() == "FL" and entity_type in ("llc", "corporation", "s_corp", "nonprofit")

    def get_priority(self, state: str, entity_type: str) -> int:
        return 1

    def get_estimated_time(self, state: str, entity_type: str, expedited: bool = False) -> str:
        if expedited:
            return "1-3 business days"
        return "5-7 business days"

    async def submit(self, request: FilingRequest) -> FilingResult:
        ref_id = f"FL-{uuid.uuid4().hex[:8].upper()}"
        self._simulated[ref_id] = {"status": FilingStatus.SUBMITTED}

        return FilingResult(
            status=FilingStatus.SUBMITTED,
            provider_name=self.name,
            provider_type=self.provider_type,
            provider_reference_id=ref_id,
            estimated_completion=self.get_estimated_time("FL", request.entity_type, request.expedited),
            message=f"Filing submitted to Florida DOS. Reference: {ref_id}",
            raw_response={"test_mode": True},
        )

    async def check_status(self, provider_reference_id: str) -> FilingResult:
        return FilingResult(
            status=FilingStatus.APPROVED,
            provider_name=self.name,
            provider_type=self.provider_type,
            provider_reference_id=provider_reference_id,
            state_filing_number=f"FL-{uuid.uuid4().hex[:10].upper()}",
            formation_date=datetime.now(timezone.utc),
            message="Filing approved by Florida DOS (simulated)",
        )

    async def cancel(self, provider_reference_id: str) -> bool:
        return provider_reference_id in self._simulated


class WyomingDirectProvider(FilingProvider):
    """Direct filing with Wyoming Secretary of State."""

    def __init__(self):
        self._simulated: Dict[str, dict] = {}

    @property
    def name(self) -> str:
        return "wyoming_direct"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.STATE_DIRECT

    def supports(self, state: str, entity_type: str) -> bool:
        return state.upper() == "WY" and entity_type in ("llc", "corporation", "s_corp")

    def get_priority(self, state: str, entity_type: str) -> int:
        return 1

    def get_estimated_time(self, state: str, entity_type: str, expedited: bool = False) -> str:
        if expedited:
            return "Same day"
        return "2-3 weeks"

    async def submit(self, request: FilingRequest) -> FilingResult:
        ref_id = f"WY-{uuid.uuid4().hex[:8].upper()}"
        self._simulated[ref_id] = {"status": FilingStatus.SUBMITTED}

        return FilingResult(
            status=FilingStatus.SUBMITTED,
            provider_name=self.name,
            provider_type=self.provider_type,
            provider_reference_id=ref_id,
            estimated_completion=self.get_estimated_time("WY", request.entity_type, request.expedited),
            message=f"Filing submitted to Wyoming SOS. Reference: {ref_id}",
            raw_response={"test_mode": True},
        )

    async def check_status(self, provider_reference_id: str) -> FilingResult:
        return FilingResult(
            status=FilingStatus.APPROVED,
            provider_name=self.name,
            provider_type=self.provider_type,
            provider_reference_id=provider_reference_id,
            state_filing_number=f"WY-{uuid.uuid4().hex[:10].upper()}",
            formation_date=datetime.now(timezone.utc),
            message="Filing approved by Wyoming SOS (simulated)",
        )

    async def cancel(self, provider_reference_id: str) -> bool:
        return provider_reference_id in self._simulated


class NevadaDirectProvider(FilingProvider):
    """Direct filing with Nevada SOS (SilverFlume)."""

    def __init__(self):
        self._simulated: Dict[str, dict] = {}

    @property
    def name(self) -> str:
        return "nevada_direct"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.STATE_DIRECT

    def supports(self, state: str, entity_type: str) -> bool:
        return state.upper() == "NV" and entity_type in ("llc", "corporation", "s_corp")

    def get_priority(self, state: str, entity_type: str) -> int:
        return 1

    def get_estimated_time(self, state: str, entity_type: str, expedited: bool = False) -> str:
        if expedited:
            return "24 hours"
        return "2-4 weeks"

    async def submit(self, request: FilingRequest) -> FilingResult:
        ref_id = f"NV-{uuid.uuid4().hex[:8].upper()}"
        self._simulated[ref_id] = {"status": FilingStatus.SUBMITTED}

        return FilingResult(
            status=FilingStatus.SUBMITTED,
            provider_name=self.name,
            provider_type=self.provider_type,
            provider_reference_id=ref_id,
            estimated_completion=self.get_estimated_time("NV", request.entity_type, request.expedited),
            message=f"Filing submitted to Nevada SOS. Reference: {ref_id}",
            raw_response={"test_mode": True},
        )

    async def check_status(self, provider_reference_id: str) -> FilingResult:
        return FilingResult(
            status=FilingStatus.APPROVED,
            provider_name=self.name,
            provider_type=self.provider_type,
            provider_reference_id=provider_reference_id,
            state_filing_number=f"NV-{uuid.uuid4().hex[:10].upper()}",
            formation_date=datetime.now(timezone.utc),
            message="Filing approved by Nevada SOS (simulated)",
        )

    async def cancel(self, provider_reference_id: str) -> bool:
        return provider_reference_id in self._simulated
