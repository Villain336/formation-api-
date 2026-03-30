from fastapi import APIRouter

from app.api.v1.endpoints import auth, orders, states, payments, documents, webhooks, compliance, admin, filing

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(states.router, prefix="/states", tags=["States & Requirements"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])
api_router.include_router(filing.router, prefix="/filing", tags=["Filing"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
