import pytest
import uuid
from decimal import Decimal
from sqlalchemy import create_engine, text
from fastapi.responses import JSONResponse

from app.core.infrastructure import session_manager, Base
from app.modules.Platform.domain.models import Tenant
from app.modules.Platform.infrastructure.persistence import TenantRepository
from app.worker import tenant_provisioning_job

# Import models & repos
from app.modules.MenuCatalog.domain.models import MenuCategory, MenuItem
from app.modules.MenuCatalog.infrastructure.persistence import MenuCategoryRepository, MenuItemRepository

# Import endpoints and request schemas directly to test routing logic and validation flows
from app.modules.MenuCatalog.api.routes_internal import (
    list_categories,
    create_category,
    update_category,
    delete_category,
    list_menu_items,
    create_menu_item,
    update_menu_item,
    delete_menu_item,
    CreateCategoryRequest,
    UpdateCategoryRequest,
    CreateMenuItemRequest,
    UpdateMenuItemRequest
)

def cleanup_tenant_db(slug: str):
    """Forcefully drops dynamic tenant databases after test execution."""
    db_name = f"iotable_tenant_{slug}"
    platform_base_url = session_manager.base_conn_string
    if "{db_name}" in platform_base_url:
        root_url = platform_base_url.format(db_name="postgres")
    else:
        r_slash = platform_base_url.rfind("/")
        root_url = platform_base_url[:r_slash + 1] + "postgres" if r_slash != -1 else f"{platform_base_url}/postgres"
        
    root_engine = create_engine(root_url).execution_options(isolation_level="AUTOCOMMIT")
    with root_engine.connect() as conn:
        try:
            conn.execute(text(f"DROP DATABASE {db_name} (FORCE)"))
        except Exception:
            pass

def test_menu_and_category_crud_operations_end_to_end():
    """Phase 7 integration test covering full menu category and product CRUD operations via internal endpoints."""
    tenant_slug = f"menu_t_{uuid.uuid4().hex[:8]}"
    
    # 1. Initialize Central Platform DB Schemas and Tenant Records
    _ = session_manager.get_platform_session()
    platform_engine = session_manager._engines["platform"]
    Base.metadata.create_all(bind=platform_engine)
    
    try:
        # 2. Provision Isolated Tenant Database
        with session_manager.platform_session() as session:
            tenant = Tenant(slug=tenant_slug, domain=f"{tenant_slug}.iotables.net", status="draft")
            TenantRepository.add(session, tenant)
            session.commit()
            
        # Run provisioningCelery job synchronously to create database and tables
        tenant_provisioning_job(tenant_slug, "owner@menu.com", seed_data=False)
        
        # 3. Create a Category via POST endpoint
        create_payload = CreateCategoryRequest(name="Başlangıçlar", display_order=1)
        cat_resp = create_category(create_payload, tenant_slug=tenant_slug, _="tenant.menu.manage")
        
        assert cat_resp.name == "Başlangıçlar"
        assert cat_resp.display_order == 1
        assert cat_resp.id is not None
        category_id = cat_resp.id
        
        # 4. List Categories via GET endpoint and assert inclusion
        cats_list = list_categories(tenant_slug=tenant_slug, _="tenant.menu.manage")
        assert len(cats_list) == 1
        assert cats_list[0].id == category_id
        assert cats_list[0].name == "Başlangıçlar"
        
        # 5. Update Category via PUT endpoint
        update_payload = UpdateCategoryRequest(name="Sıcak Başlangıçlar", display_order=2)
        updated_cat = update_category(category_id, update_payload, tenant_slug=tenant_slug, _="tenant.menu.manage")
        assert updated_cat.name == "Sıcak Başlangıçlar"
        assert updated_cat.display_order == 2
        
        # 6. Create a Menu Item inside this Category via POST endpoint
        item_payload = CreateMenuItemRequest(
            name="Mercimek Çorbası",
            price=85.00,
            category_id=category_id,
            station_code="kitchen_main"
        )
        item_resp = create_menu_item(item_payload, tenant_slug=tenant_slug, _="tenant.menu.manage")
        assert item_resp.name == "Mercimek Çorbası"
        assert item_resp.price == 85.00
        assert item_resp.category_id == category_id
        assert item_resp.status == "active"
        item_id = item_resp.id
        
        # 7. List Items via GET endpoint
        items_list = list_menu_items(tenant_slug=tenant_slug, _="tenant.menu.manage")
        assert len(items_list) == 1
        assert items_list[0].id == item_id
        assert items_list[0].name == "Mercimek Çorbası"
        
        # 8. Update Menu Item via PUT endpoint
        item_update_payload = UpdateMenuItemRequest(
            name="Süzme Mercimek Çorbası",
            price=95.00,
            category_id=category_id,
            station_code="kitchen_main",
            status="out_of_stock"
        )
        updated_item = update_menu_item(item_id, item_update_payload, tenant_slug=tenant_slug, _="tenant.menu.manage")
        assert updated_item.name == "Süzme Mercimek Çorbası"
        assert updated_item.price == 95.00
        assert updated_item.status == "out_of_stock"
        
        # 9. Verify category deletion is BLOCKED while it contains items
        block_delete_resp = delete_category(category_id, tenant_slug=tenant_slug, _="tenant.menu.manage")
        assert isinstance(block_delete_resp, JSONResponse)
        assert block_delete_resp.status_code == 400 # Bad Request
        
        # 10. Delete the Menu Item via DELETE endpoint
        delete_item_resp = delete_menu_item(item_id, tenant_slug=tenant_slug, _="tenant.menu.manage")
        assert delete_item_resp["status"] == "success"
        
        # Verify item is gone
        items_list_post = list_menu_items(tenant_slug=tenant_slug, _="tenant.menu.manage")
        assert len(items_list_post) == 0
        
        # 11. Now delete the Category successfully via DELETE endpoint
        delete_cat_resp = delete_category(category_id, tenant_slug=tenant_slug, _="tenant.menu.manage")
        assert delete_cat_resp["status"] == "success"
        
        # Verify category is gone
        cats_list_post = list_categories(tenant_slug=tenant_slug, _="tenant.menu.manage")
        assert len(cats_list_post) == 0
        
    finally:
        # 12. Cleanup database and platform rows
        cleanup_tenant_db(tenant_slug)
        with session_manager.platform_session() as session:
            t = TenantRepository.get_by_slug(session, tenant_slug)
            if t:
                session.delete(t)
