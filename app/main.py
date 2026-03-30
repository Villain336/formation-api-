"""Formation API - Business formation, registered agent, EIN, and compliance services."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API for business entity formation across all 50 US states. "
        "Supports LLC, Corporation, S-Corp, Nonprofit, LP, and LLP formation "
        "with integrated registered agent, EIN, and compliance services."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": f"{settings.BASE_URL}/docs",
        "status": "operational",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
