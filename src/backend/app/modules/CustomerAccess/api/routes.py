import uuid
import datetime
from typing import Optional
from fastapi import APIRouter, Request, Response, Depends, Cookie, Header, HTTPException, status
from pydantic import BaseModel, Field
from app.core.api import create_problem_response
from app.modules.CustomerAccess.application.services import CustomerAccessService
from app.modules.CustomerAccess.domain.models import CustomerSession

router = APIRouter(prefix="/sessions", tags=["Customer Sessions"])

# --- DEPENDENCIES ---

def get_tenant_slug(request: Request) -> str:
    """Resolves tenant slug from Host header subdomain or X-Tenant-Slug header."""
    host = request.headers.get("host", "")
    tenant_slug = None
    
    if host:
        host_clean = host.split(":")[0]
        parts = host_clean.split(".")
        if len(parts) >= 3 and parts[-2] == "iotables" and parts[-1] == "net":
            subdomain = parts[0]
            if subdomain != "platform":
                tenant_slug = subdomain
                
    if not tenant_slug:
        tenant_slug = request.headers.get("X-Tenant-Slug")
        
    if not tenant_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant slug subdomain (ör. tenant.iotables.net) veya X-Tenant-Slug header üzerinden belirtilmelidir."
        )
    return tenant_slug

async def get_active_customer_session(
    tenant_slug: str = Depends(get_tenant_slug),
    customer_session: Optional[str] = Cookie(None),
    x_customer_session_id: Optional[str] = Header(None)
) -> CustomerSession:
    """Dependency to retrieve and validate the active customer session."""
    session_id_str = customer_session or x_customer_session_id
    if not session_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Aktif müşteri oturum kimliği bulunamadı (Çerez veya X-Customer-Session-Id header eksik)."
        )
    try:
        session_id = uuid.UUID(session_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz oturum kimliği formatı."
        )
    
    try:
        cust_session = CustomerAccessService.get_current_session(tenant_slug, session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
        
    if cust_session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Müşteri işlemi için aktif bir oturum gereklidir. Oturum durumu: {cust_session.status}"
        )
        
    return cust_session

# --- SCHEMAS ---

class JoinCustomerSessionRequest(BaseModel):
    qr_token: str = Field(..., description="Taze, tek kullanımlık masa QR token değeri.")

class JoinCustomerSessionResponse(BaseModel):
    session_id: uuid.UUID
    table_id: uuid.UUID
    expires_at_utc: datetime.datetime
    extension_count: int
    max_extensions: int
    max_expires_at_utc: datetime.datetime
    cart: dict

class CustomerSessionResponse(BaseModel):
    session_id: uuid.UUID
    table_id: uuid.UUID
    status: str
    expires_at_utc: datetime.datetime
    extension_count: int
    max_extensions: int
    max_expires_at_utc: datetime.datetime
    server_time_utc: datetime.datetime

# --- ROUTES ---

@router.post("/join", response_model=JoinCustomerSessionResponse)
def join_session(
    request: JoinCustomerSessionRequest,
    response: Response,
    tenant_slug: str = Depends(get_tenant_slug)
):
    """Joins or creates a new customer ordering session using a fresh table QR token."""
    try:
        # qr_token plaintext MUST NOT be logged
        # Biz de loglarken token hash'leyebiliriz veya gizleyebiliriz
        cust_session = CustomerAccessService.join_session(tenant_slug, request.qr_token)
    except ValueError as e:
        return create_problem_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Oturuma Katılma Başarısız",
            detail=str(e),
            error_code="SESSION_JOIN_FAILED",
            instance="/sessions/join"
        )

    # Cookie set et: customer_session
    # HttpOnly, Secure, SameSite=Lax (Geliştirme ortamında Secure=False çalışması için HTTPS tespiti yapabiliriz ama testlerde veya canlıda anayasa uyarınca sets_cookie kuralları uygulanır)
    response.set_cookie(
        key="customer_session",
        value=str(cust_session.id),
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=2400 # 40 dakika max limit
    )

    return JoinCustomerSessionResponse(
        session_id=cust_session.id,
        table_id=cust_session.table_id,
        expires_at_utc=cust_session.expires_at_utc,
        extension_count=cust_session.extension_count,
        max_extensions=cust_session.max_extensions,
        max_expires_at_utc=cust_session.max_expires_at_utc,
        cart={"items": {}, "cart_version": 1} # Boş sepet döner
    )

@router.post("/extend", response_model=CustomerSessionResponse)
def extend_session(
    tenant_slug: str = Depends(get_tenant_slug),
    active_session: CustomerSession = Depends(get_active_customer_session)
):
    """Extends the current active customer session by 10 minutes if within allowed limits."""
    try:
        updated_session = CustomerAccessService.extend_session(tenant_slug, active_session.id)
    except ValueError as e:
        return create_problem_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Oturum Uzatılamadı",
            detail=str(e),
            error_code="SESSION_EXTENSION_FAILED",
            instance="/sessions/extend"
        )

    return CustomerSessionResponse(
        session_id=updated_session.id,
        table_id=updated_session.table_id,
        status=updated_session.status,
        expires_at_utc=updated_session.expires_at_utc,
        extension_count=updated_session.extension_count,
        max_extensions=updated_session.max_extensions,
        max_expires_at_utc=updated_session.max_expires_at_utc,
        server_time_utc=datetime.datetime.now(datetime.timezone.utc)
    )

@router.get("/current", response_model=CustomerSessionResponse)
def get_current(
    tenant_slug: str = Depends(get_tenant_slug),
    active_session: CustomerSession = Depends(get_active_customer_session)
):
    """Returns the details and remaining lifetime of the current active session."""
    return CustomerSessionResponse(
        session_id=active_session.id,
        table_id=active_session.table_id,
        status=active_session.status,
        expires_at_utc=active_session.expires_at_utc,
        extension_count=active_session.extension_count,
        max_extensions=active_session.max_extensions,
        max_expires_at_utc=active_session.max_expires_at_utc,
        server_time_utc=datetime.datetime.now(datetime.timezone.utc)
    )

class MenuItemResponse(BaseModel):
    id: uuid.UUID
    name: str
    price: float
    category: str
    status: str

@router.get("/menu", response_model=list[MenuItemResponse])
def get_menu(
    tenant_slug: str = Depends(get_tenant_slug),
    active_session: CustomerSession = Depends(get_active_customer_session)
):
    """Fetches all active menu items and categories for the tenant menu catalog."""
    from app.modules.MenuCatalog.infrastructure.persistence import MenuItemRepository, MenuCategoryRepository
    from typing import Dict
    
    with session_manager.tenant_session(tenant_slug) as session:
        db_categories = MenuCategoryRepository.list_all(session)
        cat_map: Dict[uuid.UUID, str] = {cat.id: cat.name for cat in db_categories}
        
        db_items = MenuItemRepository.list_all(session)
        menu_list = []
        for item in db_items:
            if item.status == "active" and item.category_id in cat_map:
                menu_list.append(MenuItemResponse(
                    id=item.id,
                    name=item.name,
                    price=float(item.price),
                    category=cat_map[item.category_id],
                    status=item.status
                ))
        return menu_list
