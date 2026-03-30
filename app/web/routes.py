"""Web routes for the marketing site, documentation, dashboard, and legal pages."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _ctx(request: Request, **kwargs) -> dict:
    """Build template context with common variables."""
    return {"request": request, "base_url": settings.BASE_URL, **kwargs}


# ============================================================
# Marketing Pages
# ============================================================

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    return templates.TemplateResponse("web/pages/home.html", _ctx(request))


@router.get("/features", response_class=HTMLResponse, include_in_schema=False)
async def features(request: Request):
    return templates.TemplateResponse("web/pages/features.html", _ctx(request))


@router.get("/pricing", response_class=HTMLResponse, include_in_schema=False)
async def pricing(request: Request):
    return templates.TemplateResponse("web/pages/pricing.html", _ctx(request))


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse("web/pages/login.html", _ctx(request))


@router.get("/signup", response_class=HTMLResponse, include_in_schema=False)
async def signup_page(request: Request):
    return templates.TemplateResponse("web/pages/signup.html", _ctx(request))


# ============================================================
# Documentation Pages
# ============================================================

@router.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def docs_overview(request: Request):
    return templates.TemplateResponse("web/docs/overview.html", _ctx(request))


@router.get("/docs/quickstart", response_class=HTMLResponse, include_in_schema=False)
async def docs_quickstart(request: Request):
    return templates.TemplateResponse("web/docs/quickstart.html", _ctx(request))


@router.get("/docs/authentication", response_class=HTMLResponse, include_in_schema=False)
async def docs_authentication(request: Request):
    return templates.TemplateResponse("web/docs/authentication.html", _ctx(request))


@router.get("/docs/api-keys", response_class=HTMLResponse, include_in_schema=False)
async def docs_api_keys(request: Request):
    return templates.TemplateResponse("web/docs/authentication.html", _ctx(request))


@router.get("/docs/api-reference", response_class=HTMLResponse, include_in_schema=False)
async def docs_api_reference(request: Request):
    return templates.TemplateResponse("web/docs/api_reference.html", _ctx(request))


@router.get("/docs/security", response_class=HTMLResponse, include_in_schema=False)
async def docs_security(request: Request):
    return templates.TemplateResponse("web/docs/security.html", _ctx(request))


@router.get("/docs/compliance-guide", response_class=HTMLResponse, include_in_schema=False)
async def docs_compliance_guide(request: Request):
    return templates.TemplateResponse("web/docs/compliance_guide.html", _ctx(request))


# Redirect common doc paths to main pages
@router.get("/docs/entities", response_class=HTMLResponse, include_in_schema=False)
@router.get("/docs/states", response_class=HTMLResponse, include_in_schema=False)
@router.get("/docs/orders", response_class=HTMLResponse, include_in_schema=False)
@router.get("/docs/order-lifecycle", response_class=HTMLResponse, include_in_schema=False)
@router.get("/docs/pricing-fees", response_class=HTMLResponse, include_in_schema=False)
@router.get("/docs/environments", response_class=HTMLResponse, include_in_schema=False)
@router.get("/docs/webhooks", response_class=HTMLResponse, include_in_schema=False)
@router.get("/docs/sdks", response_class=HTMLResponse, include_in_schema=False)
@router.get("/docs/errors", response_class=HTMLResponse, include_in_schema=False)
@router.get("/docs/rate-limits", response_class=HTMLResponse, include_in_schema=False)
@router.get("/docs/idempotency", response_class=HTMLResponse, include_in_schema=False)
@router.get("/docs/data-handling", response_class=HTMLResponse, include_in_schema=False)
@router.get("/docs/pci-compliance", response_class=HTMLResponse, include_in_schema=False)
async def docs_placeholder(request: Request):
    return templates.TemplateResponse("web/docs/overview.html", _ctx(request))


# ============================================================
# Legal Pages
# ============================================================

@router.get("/legal/terms", response_class=HTMLResponse, include_in_schema=False)
async def legal_terms(request: Request):
    return templates.TemplateResponse("web/legal/terms.html", _ctx(request))


@router.get("/legal/privacy", response_class=HTMLResponse, include_in_schema=False)
async def legal_privacy(request: Request):
    return templates.TemplateResponse("web/legal/privacy.html", _ctx(request))


@router.get("/legal/security", response_class=HTMLResponse, include_in_schema=False)
async def legal_security(request: Request):
    return templates.TemplateResponse("web/legal/security.html", _ctx(request))


@router.get("/legal/compliance", response_class=HTMLResponse, include_in_schema=False)
async def legal_compliance(request: Request):
    return templates.TemplateResponse("web/legal/compliance.html", _ctx(request))


@router.get("/legal/dpa", response_class=HTMLResponse, include_in_schema=False)
@router.get("/legal/acceptable-use", response_class=HTMLResponse, include_in_schema=False)
async def legal_placeholder(request: Request):
    return templates.TemplateResponse("web/legal/terms.html", _ctx(request))


# ============================================================
# Dashboard Pages
# ============================================================

@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_overview(request: Request):
    return templates.TemplateResponse("web/dashboard/overview.html", _ctx(request))


@router.get("/dashboard/api-keys", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_api_keys(request: Request):
    return templates.TemplateResponse("web/dashboard/api_keys.html", _ctx(request))


# Dashboard placeholder routes
@router.get("/dashboard/usage", response_class=HTMLResponse, include_in_schema=False)
@router.get("/dashboard/webhooks", response_class=HTMLResponse, include_in_schema=False)
@router.get("/dashboard/orders", response_class=HTMLResponse, include_in_schema=False)
@router.get("/dashboard/documents", response_class=HTMLResponse, include_in_schema=False)
@router.get("/dashboard/compliance", response_class=HTMLResponse, include_in_schema=False)
@router.get("/dashboard/settings", response_class=HTMLResponse, include_in_schema=False)
@router.get("/dashboard/billing", response_class=HTMLResponse, include_in_schema=False)
@router.get("/dashboard/team", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_placeholder(request: Request):
    return templates.TemplateResponse("web/dashboard/overview.html", _ctx(request))


# ============================================================
# Misc Pages
# ============================================================

@router.get("/about", response_class=HTMLResponse, include_in_schema=False)
@router.get("/contact", response_class=HTMLResponse, include_in_schema=False)
@router.get("/blog", response_class=HTMLResponse, include_in_schema=False)
@router.get("/careers", response_class=HTMLResponse, include_in_schema=False)
@router.get("/status", response_class=HTMLResponse, include_in_schema=False)
@router.get("/changelog", response_class=HTMLResponse, include_in_schema=False)
async def misc_placeholder(request: Request):
    return templates.TemplateResponse("web/pages/home.html", _ctx(request))
