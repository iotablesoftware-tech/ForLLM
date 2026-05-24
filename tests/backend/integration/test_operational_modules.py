import pytest
import uuid
from decimal import Decimal
from sqlalchemy import create_engine, text
from app.core.infrastructure import session_manager, Base
from app.modules.Platform.domain.models import Tenant, TenantProvisioningJob
from app.modules.Platform.infrastructure.persistence import TenantRepository, ProvisioningJobRepository
from app.worker import tenant_provisioning_job

# Import repositories for operational modules
from app.modules.Tenancy.domain.models import RestaurantProfile, TenantSettings
from app.modules.Tenancy.infrastructure.persistence import RestaurantProfileRepository, TenantSettingsRepository
from app.modules.Tables.domain.models import Table
from app.modules.Tables.infrastructure.persistence import TableRepository
from app.modules.Stations.domain.models import Station
from app.modules.Stations.infrastructure.persistence import StationRepository
from app.modules.MenuCatalog.domain.models import MenuCategory, MenuItem
from app.modules.MenuCatalog.infrastructure.persistence import MenuCategoryRepository, MenuItemRepository

def cleanup_tenant_db(slug: str):
    """Utility to forcefully drop dynamic tenant databases after test execution."""
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

def test_operational_modules_multi_tenant_isolation_and_routing():
    """Validates complete database-level tenant isolation, entity persistence, and domain invariants for Aşama 2."""
    slug_alpha = f"alpha_{uuid.uuid4().hex[:8]}"
    slug_beta = f"beta_{uuid.uuid4().hex[:8]}"

    # Force platform session resolution
    _ = session_manager.get_platform_session()
    platform_engine = session_manager._engines["platform"]
    Base.metadata.create_all(bind=platform_engine)

    try:
        # 1. Provision Tenant Alpha
        with session_manager.platform_session() as session:
            tenant_a = Tenant(slug=slug_alpha, domain=f"{slug_alpha}.iotables.net", status="draft")
            TenantRepository.add(session, tenant_a)
            session.commit()
            
            job_a = TenantProvisioningJob(tenant_id=tenant_a.id, status="queued")
            ProvisioningJobRepository.add(session, job_a)
            session.commit()
            
        res_a = tenant_provisioning_job(slug_alpha, "owner@alpha.com")
        assert res_a["status"] == "success"

        # 2. Provision Tenant Beta
        with session_manager.platform_session() as session:
            tenant_b = Tenant(slug=slug_beta, domain=f"{slug_beta}.iotables.net", status="draft")
            TenantRepository.add(session, tenant_b)
            session.commit()
            
            job_b = TenantProvisioningJob(tenant_id=tenant_b.id, status="queued")
            ProvisioningJobRepository.add(session, job_b)
            session.commit()
            
        res_b = tenant_provisioning_job(slug_beta, "owner@beta.com")
        assert res_b["status"] == "success"

        # 3. Setup and seed Tenant Alpha operational models
        with session_manager.tenant_session(slug_alpha) as session_a:
            # Set profile and settings
            profile = RestaurantProfile(name="Alpha Cafe", default_locale="tr-TR", default_currency="TRY")
            RestaurantProfileRepository.add(session_a, profile)
            
            settings = TenantSettings(self_ordering_active=True, station_acceptance_required=True)
            TenantSettingsRepository.add(session_a, settings)

            # Create Tables
            table_a1 = Table(table_number="Masa 1", status="active")
            TableRepository.add(session_a, table_a1)

            # Create Stations
            station_a1 = Station(code="kitchen_main", name="Ana Mutfak")
            StationRepository.add(session_a, station_a1)

            # Create MenuCategory and MenuItems
            cat_a1 = MenuCategory(name="Ana Yemekler", display_order=1)
            MenuCategoryRepository.add(session_a, cat_a1)
            session_a.commit() # Commit category first to acquire ID

            item_a1 = MenuItem(
                name="Margarita Pizza",
                price=Decimal("250.00"),
                status="active",
                category_id=cat_a1.id,
                station_code=station_a1.code
            )
            MenuItemRepository.add(session_a, item_a1)
            session_a.commit()

        # 4. Setup and seed Tenant Beta operational models (with isolated tables/menus)
        with session_manager.tenant_session(slug_beta) as session_b:
            profile_b = RestaurantProfile(name="Beta Bistro", default_locale="en-US", default_currency="USD")
            RestaurantProfileRepository.add(session_b, profile_b)
            
            settings_b = TenantSettings(self_ordering_active=False)
            TenantSettingsRepository.add(session_b, settings_b)

            table_b1 = Table(table_number="Table 99", status="restricted")
            TableRepository.add(session_b, table_b1)
            session_b.commit()

        # 5. VERIFY ISOLATION: Check that Tenant Alpha cannot see Tenant Beta's data
        with session_manager.tenant_session(slug_alpha) as session_a:
            # Alpha profile should be Alpha Cafe
            prof = RestaurantProfileRepository.get(session_a)
            assert prof is not None
            assert prof.name == "Alpha Cafe"
            assert prof.default_currency == "TRY"

            # Alpha tables should contain only Masa 1, not Table 99
            tables_a = TableRepository.list_all(session_a)
            assert len(tables_a) == 1
            assert tables_a[0].table_number == "Masa 1"

            # Alpha stations should contain kitchen_main
            stations_a = StationRepository.list_all(session_a)
            assert len(stations_a) == 1
            assert stations_a[0].code == "kitchen_main"

            # Alpha menus should contain Margarita Pizza
            items_a = MenuItemRepository.list_all(session_a)
            assert len(items_a) == 1
            assert items_a[0].name == "Margarita Pizza"
            assert items_a[0].price == Decimal("250.00")
            assert items_a[0].station_code == "kitchen_main"

        # 6. VERIFY ISOLATION: Check that Tenant Beta cannot see Tenant Alpha's data
        with session_manager.tenant_session(slug_beta) as session_b:
            prof_b = RestaurantProfileRepository.get(session_b)
            assert prof_b is not None
            assert prof_b.name == "Beta Bistro"
            assert prof_b.default_currency == "USD"

            # Beta tables should contain only Table 99
            tables_b = TableRepository.list_all(session_b)
            assert len(tables_b) == 1
            assert tables_b[0].table_number == "Table 99"
            assert tables_b[0].status == "restricted"

            # Beta should have NO stations or menu items configured
            assert len(StationRepository.list_all(session_b)) == 0
            assert len(MenuItemRepository.list_all(session_b)) == 0

    finally:
        # Clean up database files and platform records
        cleanup_tenant_db(slug_alpha)
        cleanup_tenant_db(slug_beta)
        
        with session_manager.platform_session() as session:
            ta = TenantRepository.get_by_slug(session, slug_alpha)
            if ta:
                session.delete(ta)
            tb = TenantRepository.get_by_slug(session, slug_beta)
            if tb:
                session.delete(tb)
