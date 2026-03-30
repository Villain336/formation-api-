"""Seed database with entity types and state-specific formation requirements."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.db.session import async_session
from app.models.entity import EntityType, StateRequirement


ENTITY_TYPES = [
    {
        "name": "llc",
        "display_name": "Limited Liability Company (LLC)",
        "description": "Flexible business structure combining pass-through taxation with limited liability protection. Most popular entity type for small businesses.",
    },
    {
        "name": "corporation",
        "display_name": "C Corporation",
        "description": "Separate legal entity with unlimited growth potential through stock issuance. Subject to double taxation but ideal for raising investment capital.",
    },
    {
        "name": "s_corp",
        "display_name": "S Corporation",
        "description": "Corporation that elects S-corp tax status for pass-through taxation. Limited to 100 shareholders, all must be US citizens/residents.",
    },
    {
        "name": "nonprofit",
        "display_name": "Nonprofit Corporation",
        "description": "Corporation organized for charitable, educational, religious, or scientific purposes. Eligible for tax-exempt status under IRC 501(c)(3).",
    },
    {
        "name": "lp",
        "display_name": "Limited Partnership (LP)",
        "description": "Partnership with at least one general partner (unlimited liability) and one limited partner (liability limited to investment).",
    },
    {
        "name": "llp",
        "display_name": "Limited Liability Partnership (LLP)",
        "description": "Partnership where all partners have limited liability. Common for professional services firms (law, accounting).",
    },
]

# All 50 states + DC LLC requirements
# Fees in cents, processing times in business days
STATE_LLC_DATA = [
    {
        "state_code": "AL", "state_name": "Alabama",
        "state_filing_fee": 20800, "expedited_fee": None, "name_reservation_fee": 2800,
        "standard_processing_days": 7, "expedited_processing_days": None,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 0, "annual_report_month": 4, "franchise_tax": 10000,
        "filing_agency": "Alabama Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"], "restricted_words": ["bank", "insurance", "trust"]},
    },
    {
        "state_code": "AK", "state_name": "Alaska",
        "state_filing_fee": 25000, "expedited_fee": 10000, "name_reservation_fee": 2500,
        "standard_processing_days": 10, "expedited_processing_days": 5,
        "requires_publication": False, "requires_initial_report": True,
        "annual_report_fee": 10000, "annual_report_month": 1, "franchise_tax": None,
        "filing_agency": "Alaska Division of Corporations", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "AZ", "state_name": "Arizona",
        "state_filing_fee": 5000, "expedited_fee": 3500, "name_reservation_fee": 1000,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": True, "requires_initial_report": False,
        "annual_report_fee": 0, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Arizona Corporation Commission", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"], "restricted_words": ["bank", "trust", "insurance"]},
    },
    {
        "state_code": "AR", "state_name": "Arkansas",
        "state_filing_fee": 4500, "expedited_fee": 2500, "name_reservation_fee": 2500,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 15000, "annual_report_month": 5, "franchise_tax": 15000,
        "filing_agency": "Arkansas Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "LC", "L.C.", "Limited Company"]},
    },
    {
        "state_code": "CA", "state_name": "California",
        "state_filing_fee": 7000, "expedited_fee": 35000, "name_reservation_fee": 1000,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": True,
        "annual_report_fee": 2000, "annual_report_month": None, "franchise_tax": 80000,
        "filing_agency": "California Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "Ltd. Liability Co."], "restricted_words": ["bank", "trust", "insurance", "corporation", "corp", "inc"]},
    },
    {
        "state_code": "CO", "state_name": "Colorado",
        "state_filing_fee": 5000, "expedited_fee": None, "name_reservation_fee": 2500,
        "standard_processing_days": 5, "expedited_processing_days": None,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 1000, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Colorado Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "CT", "state_name": "Connecticut",
        "state_filing_fee": 12000, "expedited_fee": 5000, "name_reservation_fee": 6000,
        "standard_processing_days": 5, "expedited_processing_days": 2,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 8000, "annual_report_month": 3, "franchise_tax": None,
        "filing_agency": "Connecticut Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "DE", "state_name": "Delaware",
        "state_filing_fee": 9000, "expedited_fee": 10000, "name_reservation_fee": 7500,
        "standard_processing_days": 3, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": None, "annual_report_month": 6, "franchise_tax": 30000,
        "filing_agency": "Delaware Division of Corporations", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"], "restricted_words": ["bank", "university", "trust"]},
    },
    {
        "state_code": "DC", "state_name": "District of Columbia",
        "state_filing_fee": 9900, "expedited_fee": 10000, "name_reservation_fee": 5000,
        "standard_processing_days": 5, "expedited_processing_days": 2,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 30000, "annual_report_month": 4, "franchise_tax": None,
        "filing_agency": "DC Department of Consumer and Regulatory Affairs", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "FL", "state_name": "Florida",
        "state_filing_fee": 12500, "expedited_fee": 5000, "name_reservation_fee": 2500,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 13875, "annual_report_month": 5, "franchise_tax": None,
        "filing_agency": "Florida Division of Corporations", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "LC"]},
    },
    {
        "state_code": "GA", "state_name": "Georgia",
        "state_filing_fee": 10000, "expedited_fee": 10000, "name_reservation_fee": 2500,
        "standard_processing_days": 7, "expedited_processing_days": 1,
        "requires_publication": True, "requires_initial_report": True,
        "annual_report_fee": 5000, "annual_report_month": 4, "franchise_tax": None,
        "filing_agency": "Georgia Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "HI", "state_name": "Hawaii",
        "state_filing_fee": 5000, "expedited_fee": 2500, "name_reservation_fee": 1000,
        "standard_processing_days": 10, "expedited_processing_days": 3,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 1500, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Hawaii Department of Commerce", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "ID", "state_name": "Idaho",
        "state_filing_fee": 10000, "expedited_fee": 2000, "name_reservation_fee": 0,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 0, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Idaho Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "Limited Company", "LC"]},
    },
    {
        "state_code": "IL", "state_name": "Illinois",
        "state_filing_fee": 15000, "expedited_fee": 10000, "name_reservation_fee": 2500,
        "standard_processing_days": 10, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 7500, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Illinois Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "L.C."]},
    },
    {
        "state_code": "IN", "state_name": "Indiana",
        "state_filing_fee": 9500, "expedited_fee": 5000, "name_reservation_fee": 2000,
        "standard_processing_days": 7, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": True,
        "annual_report_fee": 3200, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Indiana Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "IA", "state_name": "Iowa",
        "state_filing_fee": 5000, "expedited_fee": 2500, "name_reservation_fee": 1000,
        "standard_processing_days": 10, "expedited_processing_days": 3,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 6000, "annual_report_month": 4, "franchise_tax": None,
        "filing_agency": "Iowa Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "LC"]},
    },
    {
        "state_code": "KS", "state_name": "Kansas",
        "state_filing_fee": 16000, "expedited_fee": 5000, "name_reservation_fee": 3000,
        "standard_processing_days": 5, "expedited_processing_days": 2,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 5500, "annual_report_month": 4, "franchise_tax": None,
        "filing_agency": "Kansas Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "LC"]},
    },
    {
        "state_code": "KY", "state_name": "Kentucky",
        "state_filing_fee": 4000, "expedited_fee": 3000, "name_reservation_fee": 1500,
        "standard_processing_days": 5, "expedited_processing_days": 2,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 1500, "annual_report_month": 6, "franchise_tax": None,
        "filing_agency": "Kentucky Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "LA", "state_name": "Louisiana",
        "state_filing_fee": 10000, "expedited_fee": 5000, "name_reservation_fee": 2500,
        "standard_processing_days": 7, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": True,
        "annual_report_fee": 3500, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Louisiana Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "ME", "state_name": "Maine",
        "state_filing_fee": 17500, "expedited_fee": 5000, "name_reservation_fee": 2000,
        "standard_processing_days": 10, "expedited_processing_days": 2,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 8500, "annual_report_month": 6, "franchise_tax": None,
        "filing_agency": "Maine Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "MD", "state_name": "Maryland",
        "state_filing_fee": 10000, "expedited_fee": 5000, "name_reservation_fee": 2500,
        "standard_processing_days": 7, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 30000, "annual_report_month": 4, "franchise_tax": None,
        "filing_agency": "Maryland State Department of Assessments and Taxation", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "MA", "state_name": "Massachusetts",
        "state_filing_fee": 50000, "expedited_fee": 5000, "name_reservation_fee": 3000,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 50000, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Massachusetts Secretary of the Commonwealth", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "MI", "state_name": "Michigan",
        "state_filing_fee": 5000, "expedited_fee": 5000, "name_reservation_fee": 2500,
        "standard_processing_days": 7, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 2500, "annual_report_month": 2, "franchise_tax": None,
        "filing_agency": "Michigan Department of Licensing and Regulatory Affairs", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "L.C.", "LC"]},
    },
    {
        "state_code": "MN", "state_name": "Minnesota",
        "state_filing_fee": 15500, "expedited_fee": 5000, "name_reservation_fee": 3500,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 0, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Minnesota Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "MS", "state_name": "Mississippi",
        "state_filing_fee": 5000, "expedited_fee": 5000, "name_reservation_fee": 2500,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 0, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Mississippi Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "MO", "state_name": "Missouri",
        "state_filing_fee": 5000, "expedited_fee": 5000, "name_reservation_fee": 2500,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 0, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Missouri Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "LC"]},
    },
    {
        "state_code": "MT", "state_name": "Montana",
        "state_filing_fee": 7000, "expedited_fee": 2000, "name_reservation_fee": 1000,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 2000, "annual_report_month": 4, "franchise_tax": None,
        "filing_agency": "Montana Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "Limited Company", "LC"]},
    },
    {
        "state_code": "NE", "state_name": "Nebraska",
        "state_filing_fee": 10500, "expedited_fee": 5000, "name_reservation_fee": 3000,
        "standard_processing_days": 5, "expedited_processing_days": 2,
        "requires_publication": True, "requires_initial_report": False,
        "annual_report_fee": 1000, "annual_report_month": 4, "franchise_tax": None,
        "filing_agency": "Nebraska Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "NV", "state_name": "Nevada",
        "state_filing_fee": 7500, "expedited_fee": 12500, "name_reservation_fee": 2500,
        "standard_processing_days": 3, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": True,
        "annual_report_fee": 15000, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Nevada Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "Ltd Liability Co", "Limited-Liability Company"]},
    },
    {
        "state_code": "NH", "state_name": "New Hampshire",
        "state_filing_fee": 10000, "expedited_fee": 5000, "name_reservation_fee": 1500,
        "standard_processing_days": 7, "expedited_processing_days": 2,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 10000, "annual_report_month": 4, "franchise_tax": None,
        "filing_agency": "New Hampshire Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "NJ", "state_name": "New Jersey",
        "state_filing_fee": 12500, "expedited_fee": 5000, "name_reservation_fee": 5000,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 7500, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "New Jersey Division of Revenue", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "NM", "state_name": "New Mexico",
        "state_filing_fee": 5000, "expedited_fee": 10000, "name_reservation_fee": 2000,
        "standard_processing_days": 7, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 0, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "New Mexico Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "LC", "Limited Company"]},
    },
    {
        "state_code": "NY", "state_name": "New York",
        "state_filing_fee": 20000, "expedited_fee": 7500, "name_reservation_fee": 2000,
        "standard_processing_days": 7, "expedited_processing_days": 1,
        "requires_publication": True, "requires_initial_report": False,
        "annual_report_fee": 900, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "New York Department of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"], "restricted_words": ["bank", "insurance", "trust", "doctor", "lawyer"]},
    },
    {
        "state_code": "NC", "state_name": "North Carolina",
        "state_filing_fee": 12500, "expedited_fee": 10000, "name_reservation_fee": 3000,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 20000, "annual_report_month": 4, "franchise_tax": None,
        "filing_agency": "North Carolina Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "ND", "state_name": "North Dakota",
        "state_filing_fee": 13500, "expedited_fee": 5000, "name_reservation_fee": 1000,
        "standard_processing_days": 7, "expedited_processing_days": 2,
        "requires_publication": False, "requires_initial_report": True,
        "annual_report_fee": 5000, "annual_report_month": 11, "franchise_tax": None,
        "filing_agency": "North Dakota Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "OH", "state_name": "Ohio",
        "state_filing_fee": 9900, "expedited_fee": 10000, "name_reservation_fee": 3900,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 0, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Ohio Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "Ltd"]},
    },
    {
        "state_code": "OK", "state_name": "Oklahoma",
        "state_filing_fee": 10000, "expedited_fee": 2500, "name_reservation_fee": 1000,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 2500, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Oklahoma Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "LC"]},
    },
    {
        "state_code": "OR", "state_name": "Oregon",
        "state_filing_fee": 10000, "expedited_fee": 5000, "name_reservation_fee": 5000,
        "standard_processing_days": 7, "expedited_processing_days": 2,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 10000, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Oregon Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "PA", "state_name": "Pennsylvania",
        "state_filing_fee": 12500, "expedited_fee": 10000, "name_reservation_fee": 7000,
        "standard_processing_days": 10, "expedited_processing_days": 1,
        "requires_publication": True, "requires_initial_report": False,
        "annual_report_fee": 7000, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Pennsylvania Department of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "Limited Liability Co."]},
    },
    {
        "state_code": "RI", "state_name": "Rhode Island",
        "state_filing_fee": 15000, "expedited_fee": 5000, "name_reservation_fee": 5000,
        "standard_processing_days": 7, "expedited_processing_days": 2,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 5000, "annual_report_month": 11, "franchise_tax": None,
        "filing_agency": "Rhode Island Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "SC", "state_name": "South Carolina",
        "state_filing_fee": 11000, "expedited_fee": 5000, "name_reservation_fee": 2500,
        "standard_processing_days": 7, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 0, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "South Carolina Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "Limited Company", "LC"]},
    },
    {
        "state_code": "SD", "state_name": "South Dakota",
        "state_filing_fee": 15000, "expedited_fee": 5000, "name_reservation_fee": 2500,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 5000, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "South Dakota Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "TN", "state_name": "Tennessee",
        "state_filing_fee": 30000, "expedited_fee": 5000, "name_reservation_fee": 2000,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 30000, "annual_report_month": 4, "franchise_tax": None,
        "filing_agency": "Tennessee Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "TX", "state_name": "Texas",
        "state_filing_fee": 30000, "expedited_fee": 2500, "name_reservation_fee": 4000,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 0, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Texas Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "Limited Company", "LC"]},
    },
    {
        "state_code": "UT", "state_name": "Utah",
        "state_filing_fee": 7200, "expedited_fee": 7500, "name_reservation_fee": 2200,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 2000, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Utah Division of Corporations", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "L.C."]},
    },
    {
        "state_code": "VT", "state_name": "Vermont",
        "state_filing_fee": 12500, "expedited_fee": 5000, "name_reservation_fee": 2000,
        "standard_processing_days": 7, "expedited_processing_days": 2,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 3500, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Vermont Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "VA", "state_name": "Virginia",
        "state_filing_fee": 10000, "expedited_fee": 20000, "name_reservation_fee": 1000,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 5000, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Virginia State Corporation Commission", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "LC", "L.C."]},
    },
    {
        "state_code": "WA", "state_name": "Washington",
        "state_filing_fee": 18000, "expedited_fee": 5000, "name_reservation_fee": 3000,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": True,
        "annual_report_fee": 7100, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Washington Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "Limited Liability Co."]},
    },
    {
        "state_code": "WV", "state_name": "West Virginia",
        "state_filing_fee": 10000, "expedited_fee": 5000, "name_reservation_fee": 1500,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 2500, "annual_report_month": 7, "franchise_tax": None,
        "filing_agency": "West Virginia Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
    {
        "state_code": "WI", "state_name": "Wisconsin",
        "state_filing_fee": 13000, "expedited_fee": 2500, "name_reservation_fee": 1500,
        "standard_processing_days": 5, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 2500, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Wisconsin Department of Financial Institutions", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company", "LC"]},
    },
    {
        "state_code": "WY", "state_name": "Wyoming",
        "state_filing_fee": 10000, "expedited_fee": 10000, "name_reservation_fee": 5000,
        "standard_processing_days": 3, "expedited_processing_days": 1,
        "requires_publication": False, "requires_initial_report": False,
        "annual_report_fee": 6000, "annual_report_month": None, "franchise_tax": None,
        "filing_agency": "Wyoming Secretary of State", "online_filing_available": True,
        "naming_rules": {"required_suffix": ["LLC", "L.L.C.", "Limited Liability Company"]},
    },
]


async def seed_entity_types(session):
    """Insert entity types if they don't exist."""
    for et_data in ENTITY_TYPES:
        result = await session.execute(
            select(EntityType).where(EntityType.name == et_data["name"])
        )
        if not result.scalar_one_or_none():
            session.add(EntityType(**et_data))
    await session.commit()
    print(f"Seeded {len(ENTITY_TYPES)} entity types")


async def seed_state_requirements(session):
    """Insert state requirements for LLCs across all 50 states + DC."""
    count = 0
    for state_data in STATE_LLC_DATA:
        state_code = state_data["state_code"]
        entity_type = "llc"

        result = await session.execute(
            select(StateRequirement).where(
                StateRequirement.state_code == state_code,
                StateRequirement.entity_type == entity_type,
            )
        )
        if result.scalar_one_or_none():
            continue

        filing_agency_url = f"https://sos.{state_code.lower()}.gov" if state_code != "DC" else "https://dcra.dc.gov"

        req = StateRequirement(
            state_code=state_code,
            state_name=state_data["state_name"],
            entity_type=entity_type,
            state_filing_fee=state_data["state_filing_fee"],
            expedited_fee=state_data.get("expedited_fee"),
            name_reservation_fee=state_data.get("name_reservation_fee"),
            standard_processing_days=state_data["standard_processing_days"],
            expedited_processing_days=state_data.get("expedited_processing_days"),
            requires_registered_agent=True,
            requires_operating_agreement=False,
            requires_publication=state_data.get("requires_publication", False),
            requires_initial_report=state_data.get("requires_initial_report", False),
            min_members=1,
            min_directors=None,
            annual_report_fee=state_data.get("annual_report_fee"),
            annual_report_month=state_data.get("annual_report_month"),
            franchise_tax=state_data.get("franchise_tax"),
            filing_agency=state_data["filing_agency"],
            filing_agency_url=filing_agency_url,
            online_filing_available=state_data.get("online_filing_available", False),
            naming_rules=state_data.get("naming_rules"),
            required_documents={"articles_of_organization": True, "operating_agreement": False},
        )
        session.add(req)
        count += 1

    # Also seed corporation requirements for the most popular states
    corp_states = [
        ("DE", "Delaware", 8900, 10000, 3, 1, "Delaware Division of Corporations", 30000),
        ("WY", "Wyoming", 10000, 10000, 3, 1, "Wyoming Secretary of State", 5000),
        ("NV", "Nevada", 7500, 12500, 3, 1, "Nevada Secretary of State", 15000),
        ("CA", "California", 10000, 35000, 5, 1, "California Secretary of State", 80000),
        ("FL", "Florida", 7000, 5000, 5, 1, "Florida Division of Corporations", 15000),
        ("TX", "Texas", 30000, 2500, 5, 1, "Texas Secretary of State", 0),
        ("NY", "New York", 12500, 7500, 7, 1, "New York Department of State", 900),
    ]
    for code, name, fee, exp_fee, std_days, exp_days, agency, annual_fee in corp_states:
        result = await session.execute(
            select(StateRequirement).where(
                StateRequirement.state_code == code,
                StateRequirement.entity_type == "corporation",
            )
        )
        if result.scalar_one_or_none():
            continue
        req = StateRequirement(
            state_code=code,
            state_name=name,
            entity_type="corporation",
            state_filing_fee=fee,
            expedited_fee=exp_fee,
            standard_processing_days=std_days,
            expedited_processing_days=exp_days,
            requires_registered_agent=True,
            min_members=1,
            min_directors=1,
            annual_report_fee=annual_fee,
            filing_agency=agency,
            online_filing_available=True,
            naming_rules={"required_suffix": ["Inc.", "Inc", "Incorporated", "Corporation", "Corp.", "Corp", "Co."]},
            required_documents={"articles_of_incorporation": True, "bylaws": False},
        )
        session.add(req)
        count += 1

    await session.commit()
    print(f"Seeded {count} state requirements")


async def main():
    # Create all tables first
    from app.db.base import Base
    from app.db.session import engine
    import app.models  # noqa: F401 - register all models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

    async with async_session() as session:
        await seed_entity_types(session)
        await seed_state_requirements(session)
    print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(main())
