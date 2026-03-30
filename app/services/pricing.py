"""Calculate pricing for formation orders based on state, entity type, and options."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entity import StateRequirement
from app.models.order import ProcessingSpeed

# Service fees in cents
SERVICE_FEES = {
    "standard": 14900,   # $149 base formation service
    "expedited": 24900,  # $249 with expedited processing
    "rush": 34900,       # $349 rush processing
}

OPERATING_AGREEMENT_FEE = 3900  # $39
EIN_SERVICE_FEE = 7900          # $79


async def calculate_pricing(
    db: AsyncSession,
    entity_type: str,
    state_code: str,
    processing_speed: ProcessingSpeed,
    include_registered_agent: bool,
    include_ein: bool,
    include_operating_agreement: bool,
) -> dict:
    """Calculate total pricing for an order."""
    result = await db.execute(
        select(StateRequirement).where(
            StateRequirement.state_code == state_code.upper(),
            StateRequirement.entity_type == entity_type,
        )
    )
    state_req = result.scalar_one_or_none()

    state_fee = state_req.state_filing_fee if state_req else 0
    expedited_fee = 0
    if processing_speed == ProcessingSpeed.EXPEDITED and state_req and state_req.expedited_fee:
        expedited_fee = state_req.expedited_fee
    elif processing_speed == ProcessingSpeed.RUSH and state_req and state_req.expedited_fee:
        expedited_fee = state_req.expedited_fee * 2  # Double for rush

    service_fee = SERVICE_FEES.get(processing_speed.value, SERVICE_FEES["standard"])

    ra_fee = settings.REGISTERED_AGENT_ANNUAL_FEE if include_registered_agent else 0
    ein_fee = EIN_SERVICE_FEE if include_ein else 0
    oa_fee = OPERATING_AGREEMENT_FEE if include_operating_agreement else 0

    total = state_fee + service_fee + expedited_fee + ra_fee + ein_fee + oa_fee

    return {
        "state_fee": state_fee,
        "service_fee": service_fee + ein_fee + oa_fee,
        "expedited_fee": expedited_fee,
        "registered_agent_fee": ra_fee,
        "total_amount": total,
        "currency": "usd",
        "breakdown": {
            "state_filing_fee": state_fee,
            "formation_service_fee": SERVICE_FEES.get(processing_speed.value, SERVICE_FEES["standard"]),
            "state_expedited_fee": expedited_fee,
            "registered_agent_first_year": ra_fee,
            "ein_service": ein_fee,
            "operating_agreement": oa_fee,
        },
    }
