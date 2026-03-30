"""Filing Router — automatically routes orders to the best filing provider.

The router maintains a registry of all available providers and selects
the best one for each order based on:
1. State + entity type support
2. Provider priority (direct > vendor > manual)
3. Provider availability

Usage:
    router = FilingRouter()
    result = await router.submit_filing(order)
    status = await router.check_filing_status(submission_id)
"""
from __future__ import annotations

import uuid
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional, List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.filing.base import (
    FilingProvider, FilingRequest, FilingResult,
    FilingStatus, ProviderType,
)
from app.filing.providers.delaware import DelawareDirectProvider
from app.filing.providers.state_direct import (
    TexasDirectProvider, FloridaDirectProvider,
    WyomingDirectProvider, NevadaDirectProvider,
)
from app.filing.providers.manual import ManualFilingProvider
from app.models.filing import FilingSubmission, FilingStatusLog
from app.models.order import Order, OrderStatus

logger = logging.getLogger(__name__)


class FilingRouter:
    """Routes filing requests to the best available provider.

    Provider selection order:
    1. State-specific direct providers (priority 1) — DE, TX, FL, WY, NV
    2. Wholesale vendors (priority 50) — NRAI, CSC (when added)
    3. Manual filing queue (priority 999) — universal fallback
    """

    def __init__(self):
        self._providers: List[FilingProvider] = []
        self._register_default_providers()

    def _register_default_providers(self):
        """Register all available filing providers."""
        # State direct providers
        self._providers.append(DelawareDirectProvider())
        self._providers.append(TexasDirectProvider())
        self._providers.append(FloridaDirectProvider())
        self._providers.append(WyomingDirectProvider())
        self._providers.append(NevadaDirectProvider())

        # Manual queue — always last
        self._providers.append(ManualFilingProvider())

        logger.info(f"Filing router initialized with {len(self._providers)} providers")

    def register_provider(self, provider: FilingProvider):
        """Register an additional provider (e.g., NRAI, CSC)."""
        self._providers.append(provider)
        # Re-sort by priority
        self._providers.sort(key=lambda p: p.get_priority("", ""))
        logger.info(f"Registered filing provider: {provider.name}")

    def get_provider_for(self, state: str, entity_type: str) -> FilingProvider:
        """Get the best provider for a given state and entity type."""
        candidates = [
            p for p in self._providers
            if p.supports(state, entity_type)
        ]
        if not candidates:
            raise ValueError(f"No filing provider available for {entity_type} in {state}")

        # Sort by priority (lower = better)
        candidates.sort(key=lambda p: p.get_priority(state, entity_type))
        return candidates[0]

    def get_provider_info(self, state: str, entity_type: str) -> Dict:
        """Get information about which provider would handle a filing."""
        provider = self.get_provider_for(state, entity_type)
        return {
            "provider_name": provider.name,
            "provider_type": provider.provider_type.value,
            "estimated_time_standard": provider.get_estimated_time(state, entity_type, False),
            "estimated_time_expedited": provider.get_estimated_time(state, entity_type, True),
            "is_direct": provider.provider_type == ProviderType.STATE_DIRECT,
            "is_manual": provider.provider_type == ProviderType.MANUAL,
        }

    def list_providers(self) -> List[Dict]:
        """List all registered providers."""
        return [
            {
                "name": p.name,
                "type": p.provider_type.value,
            }
            for p in self._providers
        ]

    def get_coverage(self) -> Dict[str, Dict]:
        """Get filing coverage map — which provider handles which state."""
        states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
        ]
        coverage = {}
        for state in states:
            provider = self.get_provider_for(state, "llc")
            coverage[state] = {
                "provider": provider.name,
                "type": provider.provider_type.value,
                "direct": provider.provider_type == ProviderType.STATE_DIRECT,
            }
        return coverage

    async def submit_filing(
        self,
        db: AsyncSession,
        order: Order,
    ) -> FilingSubmission:
        """Submit a filing for an order.

        1. Selects the best provider
        2. Builds the filing request
        3. Submits to the provider
        4. Records the submission in the database
        5. Returns the submission record
        """
        provider = self.get_provider_for(order.state_of_formation, order.entity_type)

        # Build request from order data
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Order).options(selectinload(Order.members)).where(Order.id == order.id)
        )
        order = result.scalar_one()

        request = FilingRequest(
            order_id=order.id,
            entity_type=order.entity_type,
            state=order.state_of_formation,
            business_name=order.business_name,
            business_name_alt1=order.business_name_alt1,
            business_name_alt2=order.business_name_alt2,
            business_purpose=order.business_purpose,
            address_line1=order.business_address_line1,
            address_line2=order.business_address_line2,
            city=order.business_city,
            state_code=order.business_state,
            zip_code=order.business_zip,
            members=[
                {
                    "full_name": m.full_name,
                    "role": m.role.value if hasattr(m.role, 'value') else m.role,
                    "title": m.title,
                    "email": m.email,
                    "ownership_percentage": float(m.ownership_percentage) if m.ownership_percentage else None,
                    "address_line1": m.address_line1,
                    "city": m.city,
                    "state": m.state,
                    "zip_code": m.zip_code,
                }
                for m in order.members
            ],
            expedited=order.processing_speed.value != "standard" if hasattr(order.processing_speed, 'value') else False,
        )

        # Submit to provider
        logger.info(f"Routing order {order.order_number} to provider: {provider.name}")
        filing_result = await provider.submit(request)

        # Record in database
        submission = FilingSubmission(
            order_id=order.id,
            provider_name=provider.name,
            provider_type=provider.provider_type.value,
            provider_reference_id=filing_result.provider_reference_id,
            status=filing_result.status.value,
            status_message=filing_result.message,
            is_expedited=request.expedited,
            estimated_completion=filing_result.estimated_completion,
            submitted_at=datetime.now(timezone.utc) if filing_result.status != FilingStatus.QUEUED else None,
            request_payload=filing_result.raw_response,
        )
        db.add(submission)

        # Log the initial status
        db.add(FilingStatusLog(
            submission_id=submission.id,
            from_status=None,
            to_status=filing_result.status.value,
            message=filing_result.message,
            changed_by=f"system:router:{provider.name}",
        ))

        # Update order status to processing
        if order.status == OrderStatus.PAID:
            order.status = OrderStatus.PROCESSING
            from app.models.order import OrderStatusHistory
            db.add(OrderStatusHistory(
                order_id=order.id,
                from_status=OrderStatus.PAID.value,
                to_status=OrderStatus.PROCESSING.value,
                notes=f"Filing submitted via {provider.name}",
            ))

        await db.flush()
        return submission

    async def check_filing_status(
        self,
        db: AsyncSession,
        submission_id: uuid.UUID,
    ) -> FilingSubmission:
        """Check the status of a filing submission and update the database."""
        result = await db.execute(
            select(FilingSubmission).where(FilingSubmission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        if not submission:
            raise ValueError(f"Filing submission {submission_id} not found")

        # Find the provider
        provider = None
        for p in self._providers:
            if p.name == submission.provider_name:
                provider = p
                break

        if not provider or not submission.provider_reference_id:
            return submission

        # Check with provider
        filing_result = await provider.check_status(submission.provider_reference_id)
        old_status = submission.status

        if filing_result.status.value != old_status:
            submission.status = filing_result.status.value
            submission.status_message = filing_result.message

            if filing_result.state_filing_number:
                submission.state_filing_number = filing_result.state_filing_number
            if filing_result.formation_date:
                submission.formation_date = filing_result.formation_date
            if filing_result.rejection_reason:
                submission.rejection_reason = filing_result.rejection_reason
            if filing_result.status in (FilingStatus.APPROVED, FilingStatus.REJECTED, FilingStatus.FAILED):
                submission.completed_at = datetime.now(timezone.utc)

            # Log status change
            db.add(FilingStatusLog(
                submission_id=submission.id,
                from_status=old_status,
                to_status=filing_result.status.value,
                message=filing_result.message,
                changed_by=f"system:poll:{provider.name}",
            ))

            # Update order status if filing is complete
            if filing_result.status == FilingStatus.APPROVED:
                await self._complete_order(db, submission, filing_result)
            elif filing_result.status == FilingStatus.REJECTED:
                await self._reject_order(db, submission, filing_result)

            await db.flush()

        return submission

    async def admin_complete_manual(
        self,
        db: AsyncSession,
        submission_id: uuid.UUID,
        state_filing_number: str,
        admin_email: str,
        notes: Optional[str] = None,
    ) -> FilingSubmission:
        """Admin marks a manual filing as complete."""
        result = await db.execute(
            select(FilingSubmission).where(FilingSubmission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        if not submission:
            raise ValueError("Submission not found")

        old_status = submission.status
        submission.status = FilingStatus.APPROVED.value
        submission.state_filing_number = state_filing_number
        submission.formation_date = datetime.now(timezone.utc)
        submission.completed_at = datetime.now(timezone.utc)
        submission.admin_notes = notes

        db.add(FilingStatusLog(
            submission_id=submission.id,
            from_status=old_status,
            to_status=FilingStatus.APPROVED.value,
            message=f"Manually completed by {admin_email}. Filing #: {state_filing_number}",
            changed_by=f"admin:{admin_email}",
        ))

        filing_result = FilingResult(
            status=FilingStatus.APPROVED,
            provider_name="manual",
            provider_type=ProviderType.MANUAL,
            state_filing_number=state_filing_number,
            formation_date=submission.formation_date,
        )
        await self._complete_order(db, submission, filing_result)
        await db.flush()
        return submission

    async def _complete_order(self, db: AsyncSession, submission: FilingSubmission, result: FilingResult):
        """Update order to filed/completed when filing is approved."""
        from app.services.order_service import update_order_status, get_order
        order = await get_order(db, submission.order_id)
        if order and order.status == OrderStatus.PROCESSING:
            await update_order_status(
                db, order, OrderStatus.FILED,
                notes=f"Filed via {submission.provider_name}. Filing #: {result.state_filing_number}",
                state_filing_number=result.state_filing_number,
            )
            # Auto-complete after filing
            await update_order_status(
                db, order, OrderStatus.COMPLETED,
                notes="Formation complete. Documents and compliance tasks created.",
            )

    async def _reject_order(self, db: AsyncSession, submission: FilingSubmission, result: FilingResult):
        """Update order to rejected when filing is rejected."""
        from app.services.order_service import update_order_status, get_order
        order = await get_order(db, submission.order_id)
        if order and order.status == OrderStatus.PROCESSING:
            await update_order_status(
                db, order, OrderStatus.REJECTED,
                notes=f"Rejected by {submission.provider_name}: {result.rejection_reason}",
                rejection_reason=result.rejection_reason,
            )


# Singleton instance
filing_router = FilingRouter()
