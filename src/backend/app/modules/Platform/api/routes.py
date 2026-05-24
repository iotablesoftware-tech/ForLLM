from fastapi import APIRouter, Depends, Query, HTTPException, status
from app.core.infrastructure import session_manager
from app.modules.Platform.infrastructure.persistence import TenantRepository

router = APIRouter(prefix="/platform/tenants", tags=["Central Platform Operations"])

@router.get("/validate-domain")
def validate_domain(
    domain: str = Query(..., description="Caddy tarafından TLS sertifikası alınacak sorgulanan alan adı.")
):
    """
    Called dynamically by Caddy On-Demand TLS reverse proxy.
    Returns HTTP 200 if the domain is registered and authorized, otherwise HTTP 404.
    """
    with session_manager.platform_session() as session:
        tenant = TenantRepository.get_by_domain(session, domain)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Domain is not registered in the SaaS tenant pool."
            )
            
        # Optional: You can filter by tenant.status in ("active", "pending_activation", "draft")
        # In our case, we allow any registered tenant in the pool to get dynamic SSL
        return {
            "domain": domain,
            "status": tenant.status,
            "valid": True
        }
