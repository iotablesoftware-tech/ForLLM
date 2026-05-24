from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any, List, Optional
import logging

from app.core.api import correlation_id_middleware, create_problem_response
from app.core.domain import DomainException
from app.core.infrastructure import session_manager

# Configure structured logging standard for modular observability
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [Correlation-ID: %(correlation_id)s] %(message)s")
logger = logging.getLogger("iotable")

app = FastAPI(
    title="IoTable Modular Monolith Backend",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Register correlation tracing middleware
app.middleware("http")(correlation_id_middleware)

# --- EXCEPTION HANDLERS (RFC 7807 Problem Details Mapping) ---

@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    logger.warning(f"Domain rule violation: {exc.message} [Code: {exc.code}]")
    return create_problem_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        title="Domain Rule Violation",
        detail=exc.message,
        error_code=exc.code or "DOMAIN_RULE_VIOLATION",
        instance=str(request.url)
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning(f"Request payload validation failed: {exc}")
    errors = {f"body.{'.'.join(str(p) for p in err['loc'][1:])}": err["msg"] for err in exc.errors()}
    return create_problem_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Request Validation Failed",
        detail="The request payload contains invalid values or formats.",
        error_code="VALIDATION_FAILED",
        instance=str(request.url),
        validation_errors=errors
    )

# --- TECHNICAL OPERATIONS & HEALTH PROBES (IETF RFC UYUMU) ---

def parse_tenant_slug(host: str) -> Optional[str]:
    """Resolves tenant slug dynamically from the host header (e.g. demo.iotables.net -> demo)."""
    if not host:
        return None
    # Strip port if present
    host_clean = host.split(":")[0]
    parts = host_clean.split(".")
    if len(parts) >= 3 and parts[-2] == "iotables" and parts[-1] == "net":
        subdomain = parts[0]
        if subdomain != "platform":
            return subdomain
    return None

@app.get("/health", response_class=JSONResponse)
@app.get("/health/live", response_class=JSONResponse)
async def health_live() -> JSONResponse:
    """IETF Liveness check. Reports if backend process is responsive to HTTP traffic."""
    body = {
        "status": "pass",
        "service": "iotable-backend",
        "version": "1.0.0",
        "releaseId": "v1.0.0-baseline",
        "checks": {}
    }
    return JSONResponse(
        content=body,
        media_type="application/health+json",
        status_code=status.HTTP_200_OK
    )

@app.get("/health/ready", response_class=JSONResponse)
async def health_ready(request: Request) -> JSONResponse:
    """IETF Readiness check. Resolves database scope dynamically and verifies connectivity."""
    host = request.headers.get("host", "")
    tenant_slug = parse_tenant_slug(host)
    
    checks: Dict[str, Dict[str, str]] = {}
    is_ready = True
    
    # 1. Platform DB Connectivity Check
    try:
        with session_manager.platform_session() as session:
            # Quick database ping check
            session.execute("SELECT 1")
        checks["platform_database_connectivity"] = {
            "status": "pass",
            "component_type": "datastore"
        }
    except Exception as e:
        logger.error(f"Platform database readiness check failed: {e}")
        checks["platform_database_connectivity"] = {
            "status": "fail",
            "component_type": "datastore",
            "error": str(e)
        }
        is_ready = False

    # 2. Redis Cache Connectivity Check
    # (Simulated connection check, will be fully implemented when redis is configured)
    checks["redis_cache_connectivity"] = {
        "status": "pass",
        "component_type": "cache"
    }

    # 3. Dynamic Tenant DB Connectivity Check (if called on a tenant subdomain)
    if tenant_slug:
        try:
            with session_manager.tenant_session(tenant_slug) as session:
                session.execute("SELECT 1")
            checks[f"tenant_database_{tenant_slug}_connectivity"] = {
                "status": "pass",
                "component_type": "datastore"
            }
        except Exception as e:
            logger.error(f"Tenant database '{tenant_slug}' readiness check failed: {e}")
            checks[f"tenant_database_{tenant_slug}_connectivity"] = {
                "status": "fail",
                "component_type": "datastore",
                "error": str(e)
            }
            is_ready = False

    # Set appropriate status and HTTP code
    status_val = "pass" if is_ready else "fail"
    http_status = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    body = {
        "status": status_val,
        "service": "iotable-backend",
        "version": "1.0.0",
        "releaseId": "v1.0.0-baseline",
        "checks": checks
    }

    return JSONResponse(
        content=body,
        media_type="application/health+json",
        status_code=http_status
    )
