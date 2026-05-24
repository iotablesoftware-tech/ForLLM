import pytest
import uuid
import datetime
from decimal import Decimal
from sqlalchemy import create_engine, text
from app.core.infrastructure import session_manager, Base, redis_client
from app.modules.Platform.domain.models import Tenant, TenantProvisioningJob
from app.modules.Platform.infrastructure.persistence import TenantRepository, ProvisioningJobRepository
from app.worker import tenant_provisioning_job

# Import operational models and repos
from app.modules.Tenancy.domain.models import RestaurantProfile, TenantSettings
from app.modules.Tenancy.infrastructure.persistence import RestaurantProfileRepository, TenantSettingsRepository
from app.modules.Tables.domain.models import Table
from app.modules.Tables.infrastructure.persistence import TableRepository
from app.modules.Stations.domain.models import Station
from app.modules.Stations.infrastructure.persistence import StationRepository
from app.modules.MenuCatalog.domain.models import MenuCategory, MenuItem
from app.modules.MenuCatalog.infrastructure.persistence import MenuCategoryRepository, MenuItemRepository

# Import Phase 3 services and repos
from app.modules.CustomerAccess.domain.models import CustomerSession
from app.modules.CustomerAccess.infrastructure.persistence import CustomerSessionRepository
from app.modules.CustomerAccess.application.services import CustomerAccessService
from app.modules.Cart.infrastructure.persistence import RedisCartRepository
from app.modules.Cart.domain.models import Cart, CartItem
from app.modules.Ordering.application.services import OrderingService
from app.modules.Ordering.domain.models import BillSession, Order, StationTicket
from app.modules.Ordering.infrastructure.persistence import BillSessionRepository, OrderRepository

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

def test_customer_session_lifecycle_shared_cart_and_atomic_ordering():
    """Phase 3 integration test covering QR rotation, session TTL, optimistic locked Redis cart, and transactional postgres order submission."""
    tenant_slug = f"cust_t_{uuid.uuid4().hex[:8]}"
    
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
            
            job = TenantProvisioningJob(tenant_id=tenant.id, status="queued")
            ProvisioningJobRepository.add(session, job)
            session.commit()
            
        prov_result = tenant_provisioning_job(tenant_slug, "owner@customer-test.com")
        assert prov_result["status"] == "success"

        # 3. Seed Tenant Operational Models (Tables, Stations, Menus)
        with session_manager.tenant_session(tenant_slug) as session_t:
            # Table configuration
            table = Table(
                table_number="Masa 42",
                status="active",
                qr_token="initial_qr_token",
                qr_expires_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(minutes=5)
            )
            TableRepository.add(session_t, table)
            
            # Station configuration
            station_k = Station(code="kitchen_1", name="Mutfak 1")
            station_b = Station(code="bar_1", name="Bar 1")
            StationRepository.add(session_t, station_k)
            StationRepository.add(session_t, station_b)

            # Category setup
            category = MenuCategory(name="Gurme Pizzalar", display_order=1)
            MenuCategoryRepository.add(session_t, category)
            session_t.commit()

            # Menu Items setup
            item_pizza = MenuItem(
                name="Pizza Anatolia",
                price=Decimal("380.00"),
                status="active",
                category_id=category.id,
                station_code="kitchen_1"
            )
            item_cola = MenuItem(
                name="Soğuk Kola",
                price=Decimal("60.00"),
                status="active",
                category_id=category.id,
                station_code="bar_1"
            )
            MenuItemRepository.add(session_t, item_pizza)
            MenuItemRepository.add(session_t, item_cola)
            session_t.commit()

            # Keep IDs
            table_id = table.id
            pizza_id = str(item_pizza.id)
            cola_id = str(item_cola.id)

        # 4. TEST: Join Session (QR Rotation Validation)
        # Using correct initial_qr_token
        cust_session = CustomerAccessService.join_session(tenant_slug, "initial_qr_token")
        assert cust_session.id is not None
        assert cust_session.table_id == table_id
        assert cust_session.status == "active"
        assert cust_session.extension_count == 0
        
        # Verify that original QR token is rotated (consumed) on Table model
        with session_manager.tenant_session(tenant_slug) as session_t:
            updated_table = TableRepository.get_by_id(session_t, table_id)
            assert updated_table.qr_token != "initial_qr_token"
            assert updated_table.qr_token.startswith("qr_")
            # Storing the rotated token for negative tests
            rotated_token = updated_table.qr_token

        # Try to join again using the consumed initial_qr_token -> Should fail
        with pytest.raises(ValueError, match="Geçersiz QR kod veya masa bulunamadı"):
            CustomerAccessService.join_session(tenant_slug, "initial_qr_token")

        # 5. TEST: Session Extension (Limits and TTL)
        # Extend once
        extended_session = CustomerAccessService.extend_session(tenant_slug, cust_session.id)
        assert extended_session.extension_count == 1
        
        # Extend twice
        extended_session = CustomerAccessService.extend_session(tenant_slug, cust_session.id)
        assert extended_session.extension_count == 2
        
        # Extend thrice
        extended_session = CustomerAccessService.extend_session(tenant_slug, cust_session.id)
        assert extended_session.extension_count == 3
        
        # Try to extend 4th time -> Should fail (limit 3)
        with pytest.raises(ValueError, match="Maksimum oturum uzatma sınırına"):
            CustomerAccessService.extend_session(tenant_slug, cust_session.id)

        # 6. TEST: Redis Table-Level Collaborative Cart and Optimistic Lock
        # Initial empty cart verification
        cart = RedisCartRepository.get_cart(tenant_slug, str(table_id))
        assert cart.cart_version == 1
        assert len(cart.items) == 0

        # Add item (Pizza)
        # Correctly mock add cart item logic
        # Expected cart version matching initial = 1
        cart.items[pizza_id] = CartItem(
            menu_item_id=pizza_id,
            name="Pizza Anatolia",
            price=Decimal("380.00"),
            quantity=2,
            note="Bol kekikli",
            station_code="kitchen_1"
        )
        # Parse items dict to match model
        cart_parsed = Cart(
            cart_version=1,
            items={pizza_id: cart.items[pizza_id]}
        )
        # Save cart
        saved_cart = RedisCartRepository.save_cart(tenant_slug, str(table_id), cart_parsed, expected_version=1)
        assert saved_cart.cart_version == 2
        assert saved_cart.total_amount == Decimal("760.00")

        # Try to update/save cart with outdated expected version (expected 1 instead of 2) -> Should fail
        cart_outdated = RedisCartRepository.get_cart(tenant_slug, str(table_id))
        with pytest.raises(ValueError, match="CART_STATE_OUTOFDATE"):
            RedisCartRepository.save_cart(tenant_slug, str(table_id), cart_outdated, expected_version=1)

        # Add another item (Cola) with correct expected version = 2
        cart_current = RedisCartRepository.get_cart(tenant_slug, str(table_id))
        cart_current.items[cola_id] = CartItem(
            menu_item_id=cola_id,
            name="Soğuk Kola",
            price=Decimal("60.00"),
            quantity=3,
            note="Limonlu",
            station_code="bar_1"
        )
        saved_cart_2 = RedisCartRepository.save_cart(tenant_slug, str(table_id), cart_current, expected_version=2)
        assert saved_cart_2.cart_version == 3
        assert saved_cart_2.total_amount == Decimal("940.00")  # (380 * 2) + (60 * 3) = 760 + 180 = 940

        # 7. TEST: Transactional Order Submission (PostgreSQL Write + Redis Cart Clear + Session Offline)
        # Submit order using expected version = 3
        order = OrderingService.submit_order(
            tenant_slug=tenant_slug,
            session_id=cust_session.id,
            expected_cart_version=3,
            client_note="Masaya hızlı gelsin lütfen."
        )
        assert order.id is not None
        assert order.status == "submitted"
        assert order.total_amount == Decimal("940.00")
        assert order.order_number.startswith("ORD-")

        # Verify PostgreSQL entities inside tenant database
        with session_manager.tenant_session(tenant_slug) as session_t:
            # 1. Active BillSession opened automatically
            bill = BillSessionRepository.get_active_by_table(session_t, table_id)
            assert bill is not None
            assert bill.status == "open"

            # 2. Order tied to BillSession
            db_order = OrderRepository.get_by_id(session_t, order.id)
            assert db_order is not None
            assert db_order.bill_session_id == bill.id
            assert len(db_order.items) == 2
            
            # 3. StationTickets created and grouped by station_code
            tickets = session_t.query(StationTicket).filter(StationTicket.order_id == order.id).all()
            assert len(tickets) == 2  # kitchen_1 and bar_1
            
            # Verify tickets and ticket items
            kitchen_ticket = [t for t in tickets if t.station_code == "kitchen_1"][0]
            assert kitchen_ticket.status == "pending"
            assert len(kitchen_ticket.items) == 1
            assert kitchen_ticket.items[0].name == "Pizza Anatolia"
            assert kitchen_ticket.items[0].quantity == 2

            bar_ticket = [t for t in tickets if t.station_code == "bar_1"][0]
            assert bar_ticket.status == "pending"
            assert len(bar_ticket.items) == 1
            assert bar_ticket.items[0].name == "Soğuk Kola"
            assert bar_ticket.items[0].quantity == 3

            # 4. Customer Session moved immediately to 'offline'
            updated_session = CustomerSessionRepository.get_by_id(session_t, cust_session.id)
            assert updated_session.status == "offline"

        # Verify Redis table collaborative cart is cleared
        cleared_cart = RedisCartRepository.get_cart(tenant_slug, str(table_id))
        assert cleared_cart.cart_version == 1
        assert len(cleared_cart.items) == 0

        # 8. TEST: Negative Post-Submit Invariants
        # Try to view bill with now offline session -> Should fail
        with pytest.raises(ValueError, match="Adisyon görüntülemek için aktif oturum gereklidir"):
            OrderingService.get_current_bill_summary(tenant_slug, cust_session.id)

        # Try to submit another order with offline session -> Should fail
        with pytest.raises(ValueError, match="Sipariş gönderimi için aktif oturum gereklidir"):
            OrderingService.submit_order(
                tenant_slug=tenant_slug,
                session_id=cust_session.id,
                expected_cart_version=1
            )

    finally:
        # Clean up database files, platform records, and redis keys
        cleanup_tenant_db(tenant_slug)
        redis_client.delete(f"iotable:tenant:{tenant_slug}:table:{table_id}:cart")
        
        with session_manager.platform_session() as session:
            ta = TenantRepository.get_by_slug(session, tenant_slug)
            if ta:
                session.delete(ta)
