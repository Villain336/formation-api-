"""Formation API - Business formation, registered agent, EIN, and compliance services."""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.web.routes import router as web_router


# ============================================================
# Security Middleware
# ============================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self' https://api.stripe.com; "
            "frame-src https://js.stripe.com; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(self)"
        )
        # HSTS
        if settings.APP_ENV == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


# ============================================================
# App Setup
# ============================================================

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API for business entity formation across all 50 US states. "
        "Supports LLC, Corporation, S-Corp, Nonprofit, LP, and LLP formation "
        "with integrated registered agent, EIN, and compliance services."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# CORS - restrict in production
allowed_origins = ["*"] if settings.APP_ENV == "development" else [settings.BASE_URL]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Web routes (marketing site, docs, dashboard, legal)
app.include_router(web_router)


# ============================================================
# Health & Status Endpoints
# ============================================================

@app.get("/health", tags=["System"], include_in_schema=False)
async def health():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/health", tags=["System"])
async def api_health():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": "1.0.0", "service": settings.APP_NAME}


# ============================================================
# Robots.txt & Sitemap
# ============================================================

@app.get("/robots.txt", include_in_schema=False)
async def robots():
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        "Disallow: /dashboard/\n"
        f"Sitemap: {settings.BASE_URL}/sitemap.xml\n"
    )
    return Response(content=content, media_type="text/plain")


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap():
    base = settings.BASE_URL
    pages = [
        ("", "1.0", "weekly"),
        ("/features", "0.9", "weekly"),
        ("/pricing", "0.9", "weekly"),
        ("/docs", "0.8", "weekly"),
        ("/docs/quickstart", "0.8", "weekly"),
        ("/docs/authentication", "0.8", "weekly"),
        ("/docs/api-reference", "0.8", "weekly"),
        ("/docs/security", "0.7", "monthly"),
        ("/docs/compliance-guide", "0.7", "monthly"),
        ("/legal/terms", "0.3", "monthly"),
        ("/legal/privacy", "0.3", "monthly"),
        ("/legal/security", "0.4", "monthly"),
        ("/legal/compliance", "0.4", "monthly"),
        ("/login", "0.5", "monthly"),
        ("/signup", "0.6", "monthly"),
    ]

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for path, priority, freq in pages:
        xml += f"  <url>\n"
        xml += f"    <loc>{base}{path}</loc>\n"
        xml += f"    <priority>{priority}</priority>\n"
        xml += f"    <changefreq>{freq}</changefreq>\n"
        xml += f"  </url>\n"
    xml += "</urlset>"

    return Response(content=xml, media_type="application/xml")
