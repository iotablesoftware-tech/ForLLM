import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from decimal import Decimal
from app.core.api import create_problem_response
from app.core.infrastructure import session_manager
from app.modules.CustomerAccess.api.routes import get_tenant_slug
from app.modules.Ordering.api.routes_internal import require_staff_permission
from app.modules.MenuCatalog.domain.models import MenuCategory, MenuItem
from app.modules.MenuCatalog.infrastructure.persistence import MenuCategoryRepository, MenuItemRepository

router = APIRouter(tags=["Staff Menu & Catalog Operations"])

# --- SCHEMAS ---

class MenuCategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_order: int

class CreateCategoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Kategori adı.")
    display_order: int = Field(0, description="Kategorinin görüntülenme önceliği.")

class UpdateCategoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Kategori adı.")
    display_order: int = Field(0, description="Kategorinin görüntülenme önceliği.")

class MenuItemResponse(BaseModel):
    id: uuid.UUID
    name: str
    price: float
    status: str
    category_id: Optional[uuid.UUID]
    station_code: str

class CreateMenuItemRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Ürün adı.")
    price: float = Field(..., gt=0, description="Ürünün fiyatı (sıfırdan büyük olmalıdır).")
    category_id: uuid.UUID = Field(..., description="Ürünün ait olduğu kategori ID.")
    station_code: str = Field("kitchen_main", min_length=1, max_length=50, description="İstasyon kodu (ör. kitchen_main, bar_beverages).")

class UpdateMenuItemRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Ürün adı.")
    price: float = Field(..., gt=0, description="Ürünün fiyatı.")
    category_id: uuid.UUID = Field(..., description="Ürünün ait olduğu kategori ID.")
    station_code: str = Field(..., min_length=1, max_length=50, description="İstasyon kodu.")
    status: str = Field("active", description="Ürünün durumu: active, out_of_stock, inactive")

# --- CATEGORY ROUTES ---

@router.get("/api/internal/menu/categories", response_model=List[MenuCategoryResponse])
def list_categories(
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.menu.manage"))
):
    """Lists all menu categories for the tenant ordered by display order."""
    with session_manager.tenant_session(tenant_slug) as session:
        categories = MenuCategoryRepository.list_all(session)
        return [
            MenuCategoryResponse(
                id=cat.id,
                name=cat.name,
                display_order=cat.display_order
            )
            for cat in categories
        ]

@router.post("/api/internal/menu/categories", response_model=MenuCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CreateCategoryRequest,
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.menu.manage"))
):
    """Creates a new menu category in the tenant database."""
    with session_manager.tenant_session(tenant_slug) as session:
        new_cat = MenuCategory(
            name=payload.name,
            display_order=payload.display_order
        )
        MenuCategoryRepository.add(session, new_cat)
        session.commit()
        session.refresh(new_cat)
        return MenuCategoryResponse(
            id=new_cat.id,
            name=new_cat.name,
            display_order=new_cat.display_order
        )

@router.put("/api/internal/menu/categories/{categoryId}", response_model=MenuCategoryResponse)
def update_category(
    categoryId: uuid.UUID,
    payload: UpdateCategoryRequest,
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.menu.manage"))
):
    """Updates an existing menu category's name and priority order."""
    with session_manager.tenant_session(tenant_slug) as session:
        category = MenuCategoryRepository.get_by_id(session, categoryId)
        if not category:
            return create_problem_response(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Kategori Bulunamadı",
                detail="Belirtilen menü kategorisi bulunamadı.",
                error_code="CATEGORY_NOT_FOUND",
                instance=f"/api/internal/menu/categories/{categoryId}"
            )
        
        category.name = payload.name
        category.display_order = payload.display_order
        session.add(category)
        session.commit()
        session.refresh(category)
        return MenuCategoryResponse(
            id=category.id,
            name=category.name,
            display_order=category.display_order
        )

@router.delete("/api/internal/menu/categories/{categoryId}")
def delete_category(
    categoryId: uuid.UUID,
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.menu.manage"))
):
    """Deletes a menu category. Fails if there are active menu items associated with it."""
    with session_manager.tenant_session(tenant_slug) as session:
        category = MenuCategoryRepository.get_by_id(session, categoryId)
        if not category:
            return create_problem_response(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Kategori Bulunamadı",
                detail="Belirtilen menü kategorisi bulunamadı.",
                error_code="CATEGORY_NOT_FOUND",
                instance=f"/api/internal/menu/categories/{categoryId}"
            )
            
        # Check for active items associated
        items = MenuItemRepository.list_by_category(session, categoryId)
        if len(items) > 0:
            return create_problem_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Kategori Silinemez",
                detail="Bu kategoriye ait ürünler bulunmaktadır. Lütfen önce ürünleri silin veya başka kategoriye taşıyın.",
                error_code="CATEGORY_HAS_ITEMS",
                instance=f"/api/internal/menu/categories/{categoryId}"
            )
            
        session.delete(category)
        session.commit()
        return {"status": "success", "message": "Kategori başarıyla silindi."}

# --- PRODUCT ROUTES ---

@router.get("/api/internal/menu/items", response_model=List[MenuItemResponse])
def list_menu_items(
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.menu.manage"))
):
    """Lists all menu items in the catalog (active and inactive)."""
    with session_manager.tenant_session(tenant_slug) as session:
        items = MenuItemRepository.list_all(session)
        return [
            MenuItemResponse(
                id=item.id,
                name=item.name,
                price=float(item.price),
                status=item.status,
                category_id=item.category_id,
                station_code=item.station_code
            )
            for item in items
        ]

@router.post("/api/internal/menu/items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
def create_menu_item(
    payload: CreateMenuItemRequest,
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.menu.manage"))
):
    """Creates a new menu item inside a specific category."""
    with session_manager.tenant_session(tenant_slug) as session:
        # Check category existence
        category = MenuCategoryRepository.get_by_id(session, payload.category_id)
        if not category:
            return create_problem_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Geçersiz Kategori",
                detail="Belirtilen kategori bulunamadı.",
                error_code="CATEGORY_NOT_FOUND",
                instance="/api/internal/menu/items"
            )
            
        new_item = MenuItem(
            name=payload.name,
            price=Decimal(str(payload.price)),
            category_id=payload.category_id,
            station_code=payload.station_code,
            status="active"
        )
        MenuItemRepository.add(session, new_item)
        session.commit()
        session.refresh(new_item)
        return MenuItemResponse(
            id=new_item.id,
            name=new_item.name,
            price=float(new_item.price),
            status=new_item.status,
            category_id=new_item.category_id,
            station_code=new_item.station_code
        )

@router.put("/api/internal/menu/items/{itemId}", response_model=MenuItemResponse)
def update_menu_item(
    itemId: uuid.UUID,
    payload: UpdateMenuItemRequest,
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.menu.manage"))
):
    """Updates details of an existing menu item."""
    with session_manager.tenant_session(tenant_slug) as session:
        item = MenuItemRepository.get_by_id(session, itemId)
        if not item:
            return create_problem_response(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Ürün Bulunamadı",
                detail="Belirtilen menü ürünü bulunamadı.",
                error_code="ITEM_NOT_FOUND",
                instance=f"/api/internal/menu/items/{itemId}"
            )
            
        # Check category existence
        category = MenuCategoryRepository.get_by_id(session, payload.category_id)
        if not category:
            return create_problem_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Geçersiz Kategori",
                detail="Belirtilen kategori bulunamadı.",
                error_code="CATEGORY_NOT_FOUND",
                instance=f"/api/internal/menu/items/{itemId}"
            )
            
        if payload.status not in ("active", "out_of_stock", "inactive"):
            return create_problem_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Geçersiz Ürün Durumu",
                detail="Ürün durumu active, out_of_stock veya inactive olmalıdır.",
                error_code="INVALID_ITEM_STATUS",
                instance=f"/api/internal/menu/items/{itemId}"
            )
            
        item.name = payload.name
        item.price = Decimal(str(payload.price))
        item.category_id = payload.category_id
        item.station_code = payload.station_code
        item.status = payload.status
        
        session.add(item)
        session.commit()
        session.refresh(item)
        return MenuItemResponse(
            id=item.id,
            name=item.name,
            price=float(item.price),
            status=item.status,
            category_id=item.category_id,
            station_code=item.station_code
        )

@router.delete("/api/internal/menu/items/{itemId}")
def delete_menu_item(
    itemId: uuid.UUID,
    tenant_slug: str = Depends(get_tenant_slug),
    _: str = Depends(require_staff_permission("tenant.menu.manage"))
):
    """Deletes a menu item from the catalog."""
    with session_manager.tenant_session(tenant_slug) as session:
        item = MenuItemRepository.get_by_id(session, itemId)
        if not item:
            return create_problem_response(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Ürün Bulunamadı",
                detail="Belirtilen menü ürünü bulunamadı.",
                error_code="ITEM_NOT_FOUND",
                instance=f"/api/internal/menu/items/{itemId}"
            )
            
        session.delete(item)
        session.commit()
        return {"status": "success", "message": "Ürün başarıyla silindi."}
