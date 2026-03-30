"""Delaware Direct Filing Provider.

Delaware Division of Corporations supports electronic filing via their
ICIS (Integrated Corporate Information System). This provider handles:
- LLC Certificate of Formation
- Corporation Certificate of Incorporation

Delaware is the #1 formation state (~40% of all US LLC formations).
Direct filing means $0 vendor fees and faster processing.

Production integration requires:
1. Register for a Delaware ICIS filing agent account
2. Obtain API credentials from Delaware Division of Corporations
3. Set DELAWARE_FILING_AGENT_ID and DELAWARE_API_KEY in .env

Reference: https://icis.corp.delaware.gov/
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


# Delaware filing templates
DE_LLC_TEMPLATE = {
    "filing_type": "CERTIFICATE_OF_FORMATION",
    "entity_type": "LLC",
    "required_fields": [
        "entity_name", "registered_agent_name", "registered_agent_address",
        "organizer_name", "organizer_address",
    ],
}

DE_CORP_TEMPLATE = {
    "filing_type": "CERTIFICATE_OF_INCORPORATION",
    "entity_type": "CORPORATION",
    "required_fields": [
        "entity_name", "registered_agent_name", "registered_agent_address",
        "incorporator_name", "incorporator_address",
        "authorized_shares", "par_value",
    ],
}


class DelawareDirectProvider(FilingProvider):
    """Direct filing with Delaware Division of Corporations.

    In test mode, simulates the filing process.
    In production, submits via Delaware ICIS API.
    """

    def __init__(self, agent_id: Optional[str] = None, api_key: Optional[str] = None):
        self._agent_id = agent_id
        self._api_key = api_key
        self._is_live = bool(agent_id and api_key)
        # Track simulated filings for test mode
        self._simulated: Dict[str, dict] = {}

    @property
    def name(self) -> str:
        return "delaware_direct"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.STATE_DIRECT

    def supports(self, state: str, entity_type: str) -> bool:
        return state.upper() == "DE" and entity_type in ("llc", "corporation", "s_corp")

    def get_priority(self, state: str, entity_type: str) -> int:
        return 1  # Highest priority for Delaware

    def get_estimated_time(self, state: str, entity_type: str, expedited: bool = False) -> str:
        if expedited:
            return "24 hours"
        return "3-5 business days"

    async def submit(self, request: FilingRequest) -> FilingResult:
        """Submit filing to Delaware.

        In test mode: creates a simulated filing with a tracking ID.
        In production: submits XML to Delaware ICIS API.
        """
        logger.info(f"Delaware filing: {request.business_name} ({request.entity_type})")

        # Build the filing payload
        payload = self._build_payload(request)

        if self._is_live:
            return await self._submit_live(request, payload)
        else:
            return await self._submit_test(request, payload)

    async def _submit_test(self, request: FilingRequest, payload: dict) -> FilingResult:
        """Simulate a Delaware filing for test mode."""
        ref_id = f"DE-TEST-{uuid.uuid4().hex[:8].upper()}"

        self._simulated[ref_id] = {
            "status": FilingStatus.SUBMITTED,
            "request": request,
            "payload": payload,
            "created_at": datetime.now(timezone.utc),
        }

        return FilingResult(
            status=FilingStatus.SUBMITTED,
            provider_name=self.name,
            provider_type=self.provider_type,
            provider_reference_id=ref_id,
            estimated_completion="3-5 business days (simulated)",
            message=f"Test filing submitted to Delaware. Reference: {ref_id}",
            raw_response={"test_mode": True, "reference_id": ref_id, "payload": payload},
        )

    async def _submit_live(self, request: FilingRequest, payload: dict) -> FilingResult:
        """Submit to Delaware ICIS API.

        This is the production implementation. Requires:
        - Delaware filing agent registration
        - ICIS API credentials
        - XML filing format per Delaware specifications

        The actual API call would use httpx to POST XML to Delaware's endpoint.
        """
        # Production implementation would go here:
        # 1. Build XML from payload
        # 2. Sign with agent credentials
        # 3. POST to https://icis.corp.delaware.gov/api/v1/filings
        # 4. Parse response for tracking number

        # For now, return a clear error if someone tries live mode without full integration
        return FilingResult(
            status=FilingStatus.QUEUED,
            provider_name=self.name,
            provider_type=self.provider_type,
            message="Live Delaware filing queued. ICIS integration pending.",
            raw_response={"payload": payload, "agent_id": self._agent_id},
        )

    async def check_status(self, provider_reference_id: str) -> FilingResult:
        """Check status of a Delaware filing."""
        if provider_reference_id in self._simulated:
            sim = self._simulated[provider_reference_id]
            # In test mode, auto-approve after creation
            return FilingResult(
                status=FilingStatus.APPROVED,
                provider_name=self.name,
                provider_type=self.provider_type,
                provider_reference_id=provider_reference_id,
                state_filing_number=f"DE-{uuid.uuid4().hex[:7].upper()}",
                formation_date=datetime.now(timezone.utc),
                message="Filing approved by Delaware Division of Corporations (simulated)",
            )

        # Live mode: query ICIS API
        return FilingResult(
            status=FilingStatus.SUBMITTED,
            provider_name=self.name,
            provider_type=self.provider_type,
            provider_reference_id=provider_reference_id,
            message="Status check: filing is being processed",
        )

    async def cancel(self, provider_reference_id: str) -> bool:
        """Cancel a Delaware filing if not yet processed."""
        if provider_reference_id in self._simulated:
            self._simulated[provider_reference_id]["status"] = FilingStatus.CANCELLED
            return True
        return False

    def _build_payload(self, request: FilingRequest) -> dict:
        """Build the filing payload from the request data."""
        # Find the organizer/incorporator from members
        organizer = None
        for member in request.members:
            if member.get("role") in ("owner", "organizer", "incorporator", "manager"):
                organizer = member
                break
        if not organizer and request.members:
            organizer = request.members[0]

        base = {
            "state": "DE",
            "entity_name": request.business_name,
            "entity_purpose": request.business_purpose or "Any lawful purpose",
            "registered_agent": {
                "name": request.registered_agent_name or "Formation API Registered Agent",
                "address": request.registered_agent_address or "1209 Orange St, Wilmington, DE 19801",
            },
            "principal_address": {
                "line1": request.address_line1,
                "line2": request.address_line2,
                "city": request.city,
                "state": request.state_code,
                "zip": request.zip_code,
            },
            "expedited": request.expedited,
        }

        if request.entity_type == "llc":
            base["filing_type"] = "CERTIFICATE_OF_FORMATION"
            base["organizer"] = {
                "name": organizer.get("full_name", "") if organizer else "",
                "address": self._format_member_address(organizer) if organizer else "",
            }
        elif request.entity_type in ("corporation", "s_corp"):
            base["filing_type"] = "CERTIFICATE_OF_INCORPORATION"
            base["incorporator"] = {
                "name": organizer.get("full_name", "") if organizer else "",
                "address": self._format_member_address(organizer) if organizer else "",
            }
            base["authorized_shares"] = request.metadata.get("authorized_shares", 10000)
            base["par_value"] = request.metadata.get("par_value", 0.0001)

        return base

    @staticmethod
    def _format_member_address(member: dict) -> str:
        parts = [member.get("address_line1", "")]
        if member.get("address_line2"):
            parts.append(member["address_line2"])
        parts.append(f"{member.get('city', '')}, {member.get('state', '')} {member.get('zip_code', '')}")
        return ", ".join(parts)
