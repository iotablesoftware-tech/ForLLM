from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.core.api import create_problem_response
from app.core.infrastructure import session_manager
from app.modules.CustomerAccess.api.routes import get_tenant_slug, get_active_customer_session
from app.modules.CustomerAccess.domain.models import CustomerSession
from app.modules.Cart.domain.models import Cart, CartItem
from app.modules.Cart.infrastructure.persistence import RedisCartRepository
from app.modules.MenuCatalog.infrastructure.persistence import MenuItemRepository

router = APIRouter(prefix="/cart", tags=["Cart Operations"])

# --- SCHEMAS ---

class AddCustomerCartItemRequest(BaseModel):
    menu_item_id: str = Field(..., description="Eklenecek menü elemanının kimliği (UUID).")
    quantity: int = Field(..., description="Eklenecek adet. Pozitif olmalıdır.")
    note: Optional[str] = Field(None, description="Özel hazırlık notu.")
    expected_version: int = Field(..., description="Client tarafında en son görülen sepet versiyonu (Optimistic Lock).")

class UpdateCustomerCartItemRequest(BaseModel):
    quantity: Optional[int] = Field(None, description="Yeni adet bilgisi. Verilirse pozitif olmalıdır.")
    note: Optional[str] = Field(None, description="Yeni sepet notu.")
    expected_version: int = Field(..., description="Client tarafında en son görülen sepet versiyonu (Optimistic Lock).")

class DeleteCustomerCartItemRequest(BaseModel):
    expected_version: int = Field(..., description="Client tarafında en son görülen sepet versiyonu (Optimistic Lock).")

# --- ROUTES ---

@router.get("", response_model=Cart)
def get_cart(
    tenant_slug: str = Depends(get_tenant_slug),
    active_session: CustomerSession = Depends(get_active_customer_session)
):
    """Retrieves the shared, collaborative table-level cart for the active session."""
    return RedisCartRepository.get_cart(tenant_slug, str(active_session.table_id))

@router.post("/items", response_model=Cart)
def add_cart_item(
    payload: AddCustomerCartItemRequest,
    tenant_slug: str = Depends(get_tenant_slug),
    active_session: CustomerSession = Depends(get_active_customer_session)
):
    """Adds an orderable menu item to the shared collaborative table cart in Redis."""
    if payload.quantity <= 0:
        return create_problem_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Geçersiz Adet",
            detail="Ürün adeti pozitif bir sayı olmalıdır.",
            error_code="INVALID_QUANTITY",
            instance="/cart/items"
        )

    # 1. Menü Elemanını PostgreSQL Kiracı Veritabanından Doğrula
    with session_manager.tenant_session(tenant_slug) as db_session:
        menu_item = MenuItemRepository.list_all(db_session)
        target_item = None
        for item in menu_item:
            if str(item.id) == payload.menu_item_id:
                target_item = item
                break
                
        if not target_item:
            return create_problem_response(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Ürün Bulunamadı",
                detail="Sepete eklenmek istenen ürün bulunamadı.",
                error_code="MENU_ITEM_NOT_FOUND",
                instance="/cart/items"
            )

        if target_item.status != "active":
            return create_problem_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Ürün Aktif Değil",
                detail="Bu ürün şu an siparişe kapalıdır.",
                error_code="MENU_ITEM_INACTIVE",
                instance="/cart/items"
            )

        # Ürün bilgilerini snapshot al
        item_name = target_item.name
        item_price = target_item.price
        item_station = target_item.station_code

    # 2. Redis Sepetini Çek ve Güncelle
    table_id_str = str(active_session.table_id)
    cart = RedisCartRepository.get_cart(tenant_slug, table_id_str)
    
    # Eğer ürün zaten sepette varsa adeti arttır ve notu birleştir/ez
    if payload.menu_item_id in cart.items:
        existing_item = cart.items[payload.menu_item_id]
        existing_item.quantity += payload.quantity
        if payload.note:
            existing_item.note = payload.note
    else:
        cart.items[payload.menu_item_id] = CartItem(
            menu_item_id=payload.menu_item_id,
            name=item_name,
            price=item_price,
            quantity=payload.quantity,
            note=payload.note,
            station_code=item_station
        )

    # 3. Kaydet ve Sürüm Kontrolü Yap
    try:
        updated_cart = RedisCartRepository.save_cart(tenant_slug, table_id_str, cart, payload.expected_version)
    except ValueError as e:
        if str(e) == "CART_STATE_OUTOFDATE":
            return create_problem_response(
                status_code=status.HTTP_409_CONFLICT,
                title="Sepet Sürümü Güncel Değil",
                detail="Sepet başka bir kullanıcı tarafından güncellenmiş. Lütfen sayfayı yenileyip tekrar deneyin.",
                error_code="CART_STATE_OUTOFDATE",
                instance="/cart/items"
            )
        raise e

    return updated_cart

@router.patch("/items/{menu_item_id}", response_model=Cart)
def update_cart_item(
    menu_item_id: str,
    payload: UpdateCustomerCartItemRequest,
    tenant_slug: str = Depends(get_tenant_slug),
    active_session: CustomerSession = Depends(get_active_customer_session)
):
    """Updates quantity or note for an item inside the shared collaborative table cart."""
    if payload.quantity is not None and payload.quantity <= 0:
        return create_problem_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Geçersiz Adet",
            detail="Ürün adeti pozitif bir sayı olmalıdır.",
            error_code="INVALID_QUANTITY",
            instance=f"/cart/items/{menu_item_id}"
        )

    table_id_str = str(active_session.table_id)
    cart = RedisCartRepository.get_cart(tenant_slug, table_id_str)

    if menu_item_id not in cart.items:
        return create_problem_response(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Sepet Öğesi Bulunamadı",
            detail="Sepette güncellenmek istenen ürün bulunamadı.",
            error_code="CART_ITEM_NOT_FOUND",
            instance=f"/cart/items/{menu_item_id}"
        )

    # Değerleri güncelle
    item = cart.items[menu_item_id]
    if payload.quantity is not None:
        item.quantity = payload.quantity
    if payload.note is not None:
        item.note = payload.note

    # Kaydet
    try:
        updated_cart = RedisCartRepository.save_cart(tenant_slug, table_id_str, cart, payload.expected_version)
    except ValueError as e:
        if str(e) == "CART_STATE_OUTOFDATE":
            return create_problem_response(
                status_code=status.HTTP_409_CONFLICT,
                title="Sepet Sürümü Güncel Değil",
                detail="Sepet başka bir kullanıcı tarafından güncellenmiş.",
                error_code="CART_STATE_OUTOFDATE",
                instance=f"/cart/items/{menu_item_id}"
            )
        raise e

    return updated_cart

@router.delete("/items/{menu_item_id}", response_model=Cart)
def delete_cart_item(
    menu_item_id: str,
    payload: DeleteCustomerCartItemRequest,
    tenant_slug: str = Depends(get_tenant_slug),
    active_session: CustomerSession = Depends(get_active_customer_session)
):
    """Removes an item from the shared collaborative table cart in Redis."""
    table_id_str = str(active_session.table_id)
    cart = RedisCartRepository.get_cart(tenant_slug, table_id_str)

    if menu_item_id not in cart.items:
        return create_problem_response(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Sepet Öğesi Bulunamadı",
            detail="Sepetten silinmek istenen ürün bulunamadı.",
            error_code="CART_ITEM_NOT_FOUND",
            instance=f"/cart/items/{menu_item_id}"
        )

    # Ürünü sil
    del cart.items[menu_item_id]

    # Kaydet
    try:
        updated_cart = RedisCartRepository.save_cart(tenant_slug, table_id_str, cart, payload.expected_version)
    except ValueError as e:
        if str(e) == "CART_STATE_OUTOFDATE":
            return create_problem_response(
                status_code=status.HTTP_409_CONFLICT,
                title="Sepet Sürümü Güncel Değil",
                detail="Sepet başka bir kullanıcı tarafından güncellenmiş.",
                error_code="CART_STATE_OUTOFDATE",
                instance=f"/cart/items/{menu_item_id}"
            )
        raise e

    return updated_cart
