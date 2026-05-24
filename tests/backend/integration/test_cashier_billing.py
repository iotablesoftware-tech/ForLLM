import pytest
import uuid
import datetime
from decimal import Decimal
from sqlalchemy import create_engine, text
from fastapi import HTTPException

from app.core.infrastructure import session_manager, Base
from app.modules.Platform.domain.models import Tenant, TenantProvisioningJob
from app.modules.Platform.infrastructure.persistence import TenantRepository, ProvisioningJobRepository
from app.worker import tenant_provisioning_job

from app.modules.Tables.domain.models import Table
from app.modules.Tables.infrastructure.persistence import TableRepository
from app.modules.Stations.domain.models import Station
from app.modules.Stations.infrastructure.persistence import StationRepository
from app.modules.MenuCatalog.domain.models import MenuCategory, MenuItem
from app.modules.MenuCatalog.infrastructure.persistence import MenuCategoryRepository, MenuItemRepository

from app.modules.Ordering.application.services import OrderingService
from app.modules.Ordering.domain.models import BillSession, Order, ManualPayment, BillReopenEvent
from app.modules.Ordering.infrastructure.persistence import BillSessionRepository, OrderRepository, ManualPaymentRepository

# Import endpoints directly to test logic and schema/validation flows purely
from app.modules.Ordering.api.routes_internal import (
    get_bill_detail,
    record_manual_payment as api_record_manual_payment,
    close_bill_session as api_close_bill_session,
    reopen_bill_session as api_reopen_bill_session,
    RecordManualPaymentRequest,
    CloseBillSessionRequest,
    ReopenBillSessionRequest
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

def test_cashier_billing_manual_payments_closing_and_reopening():
    """Phase 5 integration test covering staff billing panel, manual payments, matching checks, and reopen events."""
    tenant_slug = f"cashier_t_{uuid.uuid4().hex[:8]}"
    
    # 1. CENTRAL SCHEMA INITIALIZATION
    _ = session_manager.get_platform_session()
    platform_engine = session_manager._engines["CentralPlatform"] if "CentralPlatform" in session_manager._engines else session_manager._engines["platform"]
    Base.metadata.create_all(bind=platform_engine)
    
    try:
        # 2. PROVISION TENANT
        with session_manager.platform_session() as session:
            tenant = Tenant(slug=tenant_slug, domain=f"{tenant_slug}.iotables.net", status="draft")
            TenantRepository.add(session, tenant)
            session.commit()
            
            job = TenantProvisioningJob(tenant_id=tenant.id, status="queued")
            ProvisioningJobRepository.add(session, job)
            session.commit()
            
        prov_result = tenant_provisioning_job(tenant_slug, "owner@cashier-test.com")
        assert prov_result["status"] == "success"

        # 3. SEED OPERATIONAL DATA (Table, Menu Items)
        table_id = uuid.uuid4()
        menu_item_id = uuid.uuid4()
        
        with session_manager.tenant_session(tenant_slug) as session_t:
            table = Table(
                id=table_id,
                table_number="Masa 99",
                status="active",
                qr_token="qr_token_cashier_test",
                qr_expires_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(minutes=5)
            )
            TableRepository.add(session_t, table)
            
            station = Station(code="kitchen_main", name="Mutfak")
            StationRepository.add(session_t, station)
            
            category = MenuCategory(name="Burgerler", display_order=1)
            MenuCategoryRepository.add(session_t, category)
            session_t.commit()
            
            item = MenuItem(
                id=menu_item_id,
                name="Gurme Burger",
                price=Decimal("250.00"),
                status="active",
                category_id=category.id,
                station_code="kitchen_main"
            )
            MenuItemRepository.add(session_t, item)
            session_t.commit()

        # 4. INITIALIZE A BILL SESSION BY SUBMITTING A MOCK ORDER
        with session_manager.tenant_session(tenant_slug) as session_t:
            table = TableRepository.get_by_id(session_t, table_id)
            table.qr_token = "initial_qr_token_cashier"
            table.qr_expires_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(minutes=5)
            session_t.add(table)
            session_t.commit()

        from app.modules.CustomerAccess.application.services import CustomerAccessService
        cust_session = CustomerAccessService.join_session(tenant_slug, "initial_qr_token_cashier")
        cust_session_id = cust_session.id

        from app.modules.Cart.infrastructure.persistence import RedisCartRepository
        from app.modules.Cart.domain.models import Cart, CartItem
        
        cart_item = CartItem(
            menu_item_id=str(menu_item_id),
            name="Gurme Burger",
            price=Decimal("250.00"),
            quantity=2,
            station_code="kitchen_main"
        )
        RedisCartRepository.save_cart(tenant_slug, str(table_id), Cart(cart_version=1, items={str(menu_item_id): cart_item}), expected_version=1)

        # Submit order which opens a new BillSession with total of 2 x 250.00 = 500.00
        order = OrderingService.submit_order(
            tenant_slug=tenant_slug,
            session_id=cust_session_id,
            expected_cart_version=2
        )
        assert order.status == "submitted"
        
        with session_manager.tenant_session(tenant_slug) as session_t:
            bill = BillSessionRepository.get_active_by_table(session_t, table_id)
            assert bill is not None
            assert bill.status == "open"
            bill_id = bill.id

        # 5. TEST SECURITY WRAPPERS & PERMISSION ROUTING PURELY
        # Verify required permissions function
        from app.modules.Ordering.api.routes_internal import require_staff_permission
        
        # Calling permission wrapper without values fails
        with pytest.raises(HTTPException) as excinfo:
            require_staff_permission("tenant.bills.view")(None)
        assert excinfo.value.status_code == 403

        with pytest.raises(HTTPException) as excinfo:
            require_staff_permission("tenant.bills.view")("tenant.manual_payments.record")
        assert excinfo.value.status_code == 403

        # Passing correct permissions succeeds
        perms = require_staff_permission("tenant.bills.view")("tenant.bills.view, tenant.manual_payments.record")
        assert "tenant.bills.view" in perms

        # 6. TEST ENDPOINT: GET BILL DETAILS (BSA-101)
        res = get_bill_detail(billSessionId=bill_id, tenant_slug=tenant_slug, _="tenant.bills.view")
        assert res.bill_session_id == bill_id
        assert res.total_amount == 500.00
        assert len(res.attached_orders) == 1
        assert res.status == "open"

        # 7. TEST ENDPOINT: RECORD MANUAL PAYMENT & Match checks (BSA-102)
        # Try to record partial payment (amount = 200.00 when unpaid balance is 500.00)
        pay_payload_partial = RecordManualPaymentRequest(
            amount=200.00,
            currency="TRY",
            payment_method="cash"
        )
        
        # Calling the API endpoint with partial payment returns a Conflict/Bad Request Problem Response
        prob_res = api_record_manual_payment(
            billSessionId=bill_id,
            payload=pay_payload_partial,
            tenant_slug=tenant_slug,
            _="tenant.manual_payments.record"
        )
        # Verify it returns problem response mapped by RFC 7807 helper
        assert prob_res.status_code == 400
        assert "Birebir eşleşmeyen" in prob_res.body.decode()

        # Record exact matching manual payment successfully (amount = 500.00)
        pay_payload_correct = RecordManualPaymentRequest(
            amount=500.00,
            currency="TRY",
            payment_method="cash",
            external_reference="REF_999",
            note="Kasiyer Ahmet"
        )
        res_pay = api_record_manual_payment(
            billSessionId=bill_id,
            payload=pay_payload_correct,
            tenant_slug=tenant_slug,
            _="tenant.manual_payments.record"
        )
        assert res_pay.amount == 500.00
        assert res_pay.payment_method == "cash"
        
        # 8. TEST ENDPOINT: CLOSE BILL SESSION (BSA-103)
        # Attempt to close without matching payments (let's check with direct service since we recorded 500 already)
        # Let's verify bill close endpoint succeeds now that exact matching payment is recorded
        res_close = api_close_bill_session(
            billSessionId=bill_id,
            payload=CloseBillSessionRequest(manual_payment=None, reason="Masa kapatıldı"),
            tenant_slug=tenant_slug,
            x_staff_permissions="tenant.bills.close,tenant.manual_payments.record"
        )
        assert res_close.status == "closed"
        assert len(res_close.manual_payments) == 1

        # 9. TEST ENDPOINT: REOPEN BILL SESSION (BSA-104)
        # Reopen successfully with reason
        res_reopen = api_reopen_bill_session(
            billSessionId=bill_id,
            payload=ReopenBillSessionRequest(reason="Müşteri kahve eklemek istedi"),
            tenant_slug=tenant_slug,
            _="tenant.bills.reopen"
        )
        assert res_reopen.status == "open"
        assert len(res_reopen.reopen_events) == 1
        assert res_reopen.reopen_events[0].reason == "Müşteri kahve eklemek istedi"

        # 10. TEST CONFLICT ON CREATING CONCURRENT BILLS
        # Create another closed bill session for the same table
        with session_manager.tenant_session(tenant_slug) as session_t:
            another_bill = BillSession(
                table_id=table_id,
                status="closed"
            )
            session_t.add(another_bill)
            session_t.commit()
            another_bill_id = another_bill.id

        # Reopening another closed bill fails because there is already an active/open bill session for this table
        with pytest.raises(ValueError, match="Bu masa için zaten açık veya aktif bir adisyon oturumu bulunmaktadır."):
            OrderingService.reopen_bill_session(
                tenant_slug=tenant_slug,
                bill_session_id=another_bill_id,
                reason="Gereksiz açılış"
            )

    finally:
        cleanup_tenant_db(tenant_slug)
