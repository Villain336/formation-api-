"""Document generation service for formation documents."""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.models.order import Order
from app.models.member import Member
from app.models.document import Document, DocumentType

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
OUTPUT_DIR = Path("/tmp/formation-docs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


async def generate_articles_of_organization(db: AsyncSession, order: Order) -> Document:
    """Generate Articles of Organization for an LLC."""
    result = await db.execute(
        select(Order).options(selectinload(Order.members)).where(Order.id == order.id)
    )
    order = result.scalar_one()

    template = env.get_template("articles_of_organization.html")
    organizer = next((m for m in order.members if m.role.value == "organizer"), None)
    managers = [m for m in order.members if m.role.value in ("manager", "owner")]

    html_content = template.render(
        business_name=order.business_name,
        state=order.state_of_formation,
        purpose=order.business_purpose or "The purpose of the Company is to engage in any lawful act or activity for which a limited liability company may be organized.",
        address_line1=order.business_address_line1,
        address_line2=order.business_address_line2,
        city=order.business_city,
        state_code=order.business_state,
        zip_code=order.business_zip,
        organizer=organizer,
        managers=managers,
        members=order.members,
        date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
        year=datetime.now(timezone.utc).year,
    )

    filename = f"articles_of_organization_{order.order_number}.html"
    file_path = OUTPUT_DIR / filename

    with open(file_path, "w") as f:
        f.write(html_content)

    doc = Document(
        order_id=order.id,
        doc_type=DocumentType.ARTICLES_OF_ORGANIZATION,
        filename=filename,
        file_path=str(file_path),
        file_size=os.path.getsize(file_path),
        mime_type="text/html",
    )
    db.add(doc)
    await db.flush()
    return doc


async def generate_operating_agreement(db: AsyncSession, order: Order) -> Document:
    """Generate Operating Agreement for an LLC."""
    result = await db.execute(
        select(Order).options(selectinload(Order.members)).where(Order.id == order.id)
    )
    order = result.scalar_one()

    template = env.get_template("operating_agreement.html")
    members = [m for m in order.members if m.role.value in ("owner", "member", "manager")]

    html_content = template.render(
        business_name=order.business_name,
        state=order.state_of_formation,
        address_line1=order.business_address_line1,
        city=order.business_city,
        state_code=order.business_state,
        zip_code=order.business_zip,
        members=members,
        date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
        year=datetime.now(timezone.utc).year,
        management_type="member-managed" if len(members) <= 2 else "manager-managed",
    )

    filename = f"operating_agreement_{order.order_number}.html"
    file_path = OUTPUT_DIR / filename

    with open(file_path, "w") as f:
        f.write(html_content)

    doc = Document(
        order_id=order.id,
        doc_type=DocumentType.OPERATING_AGREEMENT,
        filename=filename,
        file_path=str(file_path),
        file_size=os.path.getsize(file_path),
        mime_type="text/html",
    )
    db.add(doc)
    await db.flush()
    return doc


async def generate_articles_of_incorporation(db: AsyncSession, order: Order) -> Document:
    """Generate Articles of Incorporation for a Corporation."""
    result = await db.execute(
        select(Order).options(selectinload(Order.members)).where(Order.id == order.id)
    )
    order = result.scalar_one()

    template = env.get_template("articles_of_incorporation.html")
    incorporator = next((m for m in order.members if m.role.value == "incorporator"), None)
    directors = [m for m in order.members if m.role.value == "director"]

    html_content = template.render(
        business_name=order.business_name,
        state=order.state_of_formation,
        purpose=order.business_purpose or "The purpose of the Corporation is to engage in any lawful act or activity for which corporations may be organized.",
        address_line1=order.business_address_line1,
        city=order.business_city,
        state_code=order.business_state,
        zip_code=order.business_zip,
        incorporator=incorporator,
        directors=directors,
        shares_authorized=10000000,
        par_value="0.0001",
        date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
    )

    filename = f"articles_of_incorporation_{order.order_number}.html"
    file_path = OUTPUT_DIR / filename

    with open(file_path, "w") as f:
        f.write(html_content)

    doc = Document(
        order_id=order.id,
        doc_type=DocumentType.ARTICLES_OF_INCORPORATION,
        filename=filename,
        file_path=str(file_path),
        file_size=os.path.getsize(file_path),
        mime_type="text/html",
    )
    db.add(doc)
    await db.flush()
    return doc
