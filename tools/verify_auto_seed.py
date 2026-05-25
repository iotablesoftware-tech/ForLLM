import sys
import os
import uuid
from sqlalchemy import create_engine, text

# Append src/backend to python path so imports resolve cleanly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/backend")))

from app.core.infrastructure import session_manager, Base
from app.modules.Platform.domain.models import Tenant
from app.modules.Platform.infrastructure.persistence import TenantRepository
from app.worker import tenant_provisioning_job
from app.modules.MenuCatalog.domain.models import MenuCategory, MenuItem

def cleanup_db(slug: str):
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
            print(f"Dropped test database '{db_name}'.")
        except Exception as e:
            print(f"Cleanup warning (DB drop): {e}")

def main():
    test_slug = f"verify_{uuid.uuid4().hex[:6]}"
    print(f"Provisioning test tenant with slug: {test_slug}")
    
    # 1. Create Tenant registry in platform control-plane
    with session_manager.platform_session() as session:
        # Check if already exists (highly unlikely)
        existing = TenantRepository.get_by_slug(session, test_slug)
        if existing:
            session.delete(existing)
            session.commit()
            
        tenant = Tenant(slug=test_slug, domain=f"{test_slug}.iotables.net", status="draft")
        TenantRepository.add(session, tenant)
        session.commit()
        print("Tenant record registered in platform database.")
        
    try:
        # 2. Run Celery provisioning task synchronously
        print("Triggering tenant_provisioning_job synchronously...")
        result = tenant_provisioning_job(test_slug, "owner@testverify.com")
        print("Provisioning job result:", result)
        
        # 3. Query tenant database to verify seeded categories and products count
        print("Connecting to the newly created tenant database...")
        with session_manager.tenant_session(test_slug) as tenant_session:
            cats = tenant_session.query(MenuCategory).all()
            items = tenant_session.query(MenuItem).all()
            
            print(f"Seeding Verification Success!")
            print(f"  Categories seeded: {len(cats)}")
            print(f"  Menu items seeded: {len(items)}")
            
            assert len(cats) == 18, f"Expected 18 categories, got {len(cats)}"
            assert len(items) > 100, f"Expected >100 menu items, got {len(items)}"
            
            # Print sample categories and items
            print("\nSample categories seeded:")
            for c in cats[:5]:
                print(f"  - {c.name} (order: {c.display_order})")
                
            print("\nSample items seeded:")
            for item in items[:5]:
                print(f"  - {item.name} | Price: ₺{item.price} | Station: {item.station_code}")
                
    except Exception as e:
        print("VERIFICATION FAILED:", e)
        cleanup_db(test_slug)
        with session_manager.platform_session() as session:
            t = TenantRepository.get_by_slug(session, test_slug)
            if t:
                session.delete(t)
        sys.exit(1)
        
    # 4. Clean up
    print("\nVerification completed successfully. Cleaning up test database and records...")
    cleanup_db(test_slug)
    with session_manager.platform_session() as session:
        t = TenantRepository.get_by_slug(session, test_slug)
        if t:
            session.delete(t)
            session.commit()
    print("Cleanup completed.")

if __name__ == "__main__":
    main()
