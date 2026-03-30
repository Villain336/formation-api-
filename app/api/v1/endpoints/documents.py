"""Document generation and retrieval endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.services.document_service import (
    generate_articles_of_organization,
    generate_operating_agreement,
    generate_articles_of_incorporation,
)
from app.services.order_service import get_order

router = APIRouter()


@router.post("/{order_id}/generate")
async def generate_documents(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate formation documents for an order."""
    order = await get_order(db, order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    generated = []

    if order.entity_type == "llc":
        doc = await generate_articles_of_organization(db, order)
        generated.append({"type": doc.doc_type.value, "filename": doc.filename})

        if order.include_operating_agreement:
            doc = await generate_operating_agreement(db, order)
            generated.append({"type": doc.doc_type.value, "filename": doc.filename})

    elif order.entity_type in ("corporation", "s_corp"):
        doc = await generate_articles_of_incorporation(db, order)
        generated.append({"type": doc.doc_type.value, "filename": doc.filename})

    return {"order_id": str(order_id), "documents": generated}


@router.get("/{order_id}")
async def list_documents(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for an order."""
    order = await get_order(db, order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    result = await db.execute(
        select(Document).where(Document.order_id == order_id).order_by(Document.generated_at)
    )
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "type": d.doc_type.value,
            "filename": d.filename,
            "file_size": d.file_size,
            "generated_at": d.generated_at.isoformat(),
        }
        for d in docs
    ]


@router.get("/{order_id}/download/{document_id}")
async def download_document(
    order_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a specific document."""
    order = await get_order(db, order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.order_id == order_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return FileResponse(
        path=doc.file_path,
        filename=doc.filename,
        media_type=doc.mime_type,
    )
