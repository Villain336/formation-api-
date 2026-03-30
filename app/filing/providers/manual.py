"""Manual Filing Queue Provider.

Fallback provider for states without direct API integration.
Orders go into a queue that admins process manually through
each state's Secretary of State website.

This is the universal fallback — it supports ALL states and entity types.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict

from app.filing.base import (
    FilingProvider, FilingRequest, FilingResult,
    FilingStatus, ProviderType,
)

logger = logging.getLogger(__name__)

# Instructions for admins on how to file in each state
STATE_FILING_INSTRUCTIONS = {
    "AL": {"url": "https://www.sos.alabama.gov/business-entities", "method": "Online portal"},
    "AK": {"url": "https://www.commerce.alaska.gov/cbp/main/", "method": "Online portal"},
    "AZ": {"url": "https://ecorp.azcc.gov/", "method": "Online portal"},
    "AR": {"url": "https://www.sos.arkansas.gov/corps/search_all.php", "method": "Online or mail"},
    "CA": {"url": "https://bizfileonline.sos.ca.gov/", "method": "Online portal (bizfile)"},
    "CO": {"url": "https://www.sos.state.co.us/biz/", "method": "Online portal"},
    "CT": {"url": "https://business.ct.gov/", "method": "Online portal"},
    "DE": {"url": "https://icis.corp.delaware.gov/", "method": "Online or mail"},
    "FL": {"url": "https://dos.fl.gov/sunbiz/", "method": "Online portal (Sunbiz)"},
    "GA": {"url": "https://ecorp.sos.ga.gov/", "method": "Online portal"},
    "HI": {"url": "https://hbe.ehawaii.gov/", "method": "Online portal"},
    "ID": {"url": "https://sosbiz.idaho.gov/", "method": "Online portal"},
    "IL": {"url": "https://www.ilsos.gov/departments/business_services/", "method": "Online or mail"},
    "IN": {"url": "https://inbiz.in.gov/", "method": "Online portal (INBiz)"},
    "IA": {"url": "https://sos.iowa.gov/business/", "method": "Online portal"},
    "KS": {"url": "https://www.sos.ks.gov/business/", "method": "Online portal"},
    "KY": {"url": "https://www.sos.ky.gov/bus/", "method": "Online portal"},
    "LA": {"url": "https://www.sos.la.gov/BusinessServices/", "method": "Online portal (GEAUXBIZ)"},
    "ME": {"url": "https://www.maine.gov/sos/cec/corp/", "method": "Online portal"},
    "MD": {"url": "https://egov.maryland.gov/BusinessExpress", "method": "Online portal"},
    "MA": {"url": "https://www.sec.state.ma.us/cor/", "method": "Online or mail"},
    "MI": {"url": "https://cofs.lara.state.mi.us/", "method": "Online portal (COFS)"},
    "MN": {"url": "https://mblsportal.sos.state.mn.us/", "method": "Online portal"},
    "MS": {"url": "https://www.sos.ms.gov/business-services", "method": "Online portal"},
    "MO": {"url": "https://bsd.sos.mo.gov/", "method": "Online portal"},
    "MT": {"url": "https://sosmt.gov/business/", "method": "Online portal"},
    "NE": {"url": "https://www.nebraska.gov/sos/corp/", "method": "Online portal"},
    "NV": {"url": "https://esos.nv.gov/", "method": "Online portal (SilverFlume)"},
    "NH": {"url": "https://quickstart.sos.nh.gov/", "method": "Online portal (QuickStart)"},
    "NJ": {"url": "https://www.njportal.com/DOR/BusinessFormation", "method": "Online portal"},
    "NM": {"url": "https://portal.sos.state.nm.us/", "method": "Online portal"},
    "NY": {"url": "https://www.dos.ny.gov/corps/", "method": "Online or mail"},
    "NC": {"url": "https://www.sosnc.gov/online_services/search/by_title/_Business_Registration", "method": "Online portal"},
    "ND": {"url": "https://firststop.sos.nd.gov/", "method": "Online portal (FirstStop)"},
    "OH": {"url": "https://bsportal.ohiosos.gov/", "method": "Online portal"},
    "OK": {"url": "https://www.sos.ok.gov/business/", "method": "Online portal"},
    "OR": {"url": "https://sos.oregon.gov/business/", "method": "Online portal"},
    "PA": {"url": "https://www.dos.pa.gov/BusinessCharities/Business/RegistrationForms/", "method": "Online or mail"},
    "RI": {"url": "https://business.sos.ri.gov/", "method": "Online portal"},
    "SC": {"url": "https://businessfilings.sc.gov/", "method": "Online portal"},
    "SD": {"url": "https://sdsos.gov/business-services/", "method": "Online portal"},
    "TN": {"url": "https://tnbear.tn.gov/", "method": "Online portal"},
    "TX": {"url": "https://direct.sos.state.tx.us/", "method": "Online portal (SOSDirect)"},
    "UT": {"url": "https://secure.utah.gov/bes/", "method": "Online portal"},
    "VT": {"url": "https://sos.vermont.gov/corporations/", "method": "Online or mail"},
    "VA": {"url": "https://cis.scc.virginia.gov/", "method": "Online portal (Clerk's Information System)"},
    "WA": {"url": "https://www.sos.wa.gov/corps/", "method": "Online portal"},
    "WV": {"url": "https://sos.wv.gov/business/", "method": "Online portal"},
    "WI": {"url": "https://www.wdfi.org/corporations/", "method": "Online portal"},
    "WY": {"url": "https://wyobiz.wyo.gov/", "method": "Online portal"},
    "DC": {"url": "https://corponline.dcra.dc.gov/", "method": "Online portal"},
}


class ManualFilingProvider(FilingProvider):
    """Manual filing queue — universal fallback for all states.

    Creates a queue item that admins process by hand through
    each state's Secretary of State website. Includes filing
    instructions and direct links for each state.
    """

    def __init__(self):
        self._queue: Dict[str, dict] = {}

    @property
    def name(self) -> str:
        return "manual"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.MANUAL

    def supports(self, state: str, entity_type: str) -> bool:
        # Manual filing supports everything
        return True

    def get_priority(self, state: str, entity_type: str) -> int:
        return 999  # Lowest priority — only used when no direct provider exists

    def get_estimated_time(self, state: str, entity_type: str, expedited: bool = False) -> str:
        if expedited:
            return "1-3 business days"
        return "5-15 business days"

    async def submit(self, request: FilingRequest) -> FilingResult:
        """Add order to the manual filing queue."""
        ref_id = f"MQ-{uuid.uuid4().hex[:8].upper()}"
        state = request.state.upper()

        instructions = STATE_FILING_INSTRUCTIONS.get(state, {
            "url": "Check state Secretary of State website",
            "method": "Varies",
        })

        queue_item = {
            "ref_id": ref_id,
            "order_id": str(request.order_id),
            "state": state,
            "entity_type": request.entity_type,
            "business_name": request.business_name,
            "expedited": request.expedited,
            "status": FilingStatus.QUEUED,
            "filing_instructions": instructions,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "request_data": {
                "business_name": request.business_name,
                "business_purpose": request.business_purpose,
                "address": f"{request.address_line1}, {request.city}, {request.state_code} {request.zip_code}",
                "members": [
                    {"name": m.get("full_name"), "role": m.get("role"), "email": m.get("email")}
                    for m in request.members
                ],
            },
        }
        self._queue[ref_id] = queue_item

        logger.info(f"Manual queue: {request.business_name} in {state} -> {ref_id}")

        return FilingResult(
            status=FilingStatus.QUEUED,
            provider_name=self.name,
            provider_type=self.provider_type,
            provider_reference_id=ref_id,
            estimated_completion=self.get_estimated_time(state, request.entity_type, request.expedited),
            message=f"Order queued for manual filing in {state}. Admin will process via {instructions['method']}.",
            raw_response={
                "queue_item": queue_item,
                "filing_url": instructions.get("url"),
                "filing_method": instructions.get("method"),
            },
        )

    async def check_status(self, provider_reference_id: str) -> FilingResult:
        """Check queue status."""
        if provider_reference_id in self._queue:
            item = self._queue[provider_reference_id]
            return FilingResult(
                status=FilingStatus(item["status"]),
                provider_name=self.name,
                provider_type=self.provider_type,
                provider_reference_id=provider_reference_id,
                message=f"Manual filing queue status: {item['status']}",
            )

        return FilingResult(
            status=FilingStatus.QUEUED,
            provider_name=self.name,
            provider_type=self.provider_type,
            provider_reference_id=provider_reference_id,
            message="Filing is in the manual queue",
        )

    async def cancel(self, provider_reference_id: str) -> bool:
        if provider_reference_id in self._queue:
            self._queue[provider_reference_id]["status"] = FilingStatus.CANCELLED
            return True
        return False

    def get_queue(self, status_filter: str = None) -> list:
        """Get all items in the manual queue, optionally filtered by status."""
        items = list(self._queue.values())
        if status_filter:
            items = [i for i in items if i["status"] == status_filter]
        return sorted(items, key=lambda x: x["created_at"])

    async def admin_update_status(
        self,
        provider_reference_id: str,
        new_status: FilingStatus,
        state_filing_number: str = None,
        rejection_reason: str = None,
        admin_notes: str = None,
    ) -> FilingResult:
        """Admin updates the status of a manual filing."""
        if provider_reference_id not in self._queue:
            return FilingResult(
                status=FilingStatus.FAILED,
                provider_name=self.name,
                provider_type=self.provider_type,
                message=f"Queue item {provider_reference_id} not found",
            )

        item = self._queue[provider_reference_id]
        item["status"] = new_status
        if admin_notes:
            item["admin_notes"] = admin_notes

        result = FilingResult(
            status=new_status,
            provider_name=self.name,
            provider_type=self.provider_type,
            provider_reference_id=provider_reference_id,
            state_filing_number=state_filing_number,
            rejection_reason=rejection_reason,
            message=f"Status updated to {new_status.value} by admin",
        )

        if new_status == FilingStatus.APPROVED:
            result.formation_date = datetime.now(timezone.utc)

        return result
