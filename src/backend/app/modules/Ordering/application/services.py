import uuid
import datetime
import secrets
from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.infrastructure import session_manager
from app.modules.CustomerAccess.domain.models import CustomerSession
from app.modules.CustomerAccess.infrastructure.persistence import CustomerSessionRepository
from app.modules.Cart.infrastructure.persistence import RedisCartRepository
from app.modules.MenuCatalog.domain.models import MenuItem
from app.modules.MenuCatalog.infrastructure.persistence import MenuItemRepository
from app.modules.Ordering.domain.models import BillSession, Order, OrderItem, StationTicket, StationTicketItem, ManualPayment, BillReopenEvent
from app.modules.Ordering.infrastructure.persistence import BillSessionRepository, OrderRepository, ManualPaymentRepository, BillReopenEventRepository

class OrderingService:
    @staticmethod
    def submit_order(
        tenant_slug: str,
        session_id: uuid.UUID,
        expected_cart_version: int,
        client_note: Optional[str] = None
    ) -> Order:
        if not tenant_slug or not session_id:
            raise ValueError("Tenant slug ve oturum ID zorunludur.")

        # 1. PostgreSQL Tenant Bağlantısını Başlat (Transactional Boundary)
        with session_manager.tenant_session(tenant_slug) as session:
            # 2. Müşteri Oturumunu Doğrula
            cust_session = CustomerSessionRepository.get_by_id(session, session_id)
            if not cust_session:
                raise ValueError("Oturum bulunamadı.")
            
            if cust_session.status != "active":
                raise ValueError(f"Sipariş gönderimi için aktif oturum gereklidir. Oturum statüsü: {cust_session.status}")

            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            if cust_session.expires_at_utc <= now:
                cust_session.status = "expired"
                session.add(cust_session)
                session.commit()
                raise ValueError("Oturum süresi dolmuş. Sipariş gönderilemez.")

            # 3. Redis Masa Sepetini Çek ve Doğrula
            table_id_str = str(cust_session.table_id)
            cart = RedisCartRepository.get_cart(tenant_slug, table_id_str)
            
            if not cart.items:
                raise ValueError("Boş bir sepet sipariş olarak gönderilemez.")

            if cart.cart_version != expected_cart_version:
                raise ValueError("CART_STATE_OUTOFDATE")

            # 4. Sepetteki Ürünlerin Fiyatlarını ve Rotalarını Revalidate Et
            total_amount = Decimal("0.00")
            validated_items = []
            
            # Tüm menü elemanlarını çekip eşleştir
            db_menu_items = MenuItemRepository.list_all(session)
            db_menu_dict = {str(item.id): item for item in db_menu_items}

            for cart_item_id, item in cart.items.items():
                db_item = db_menu_dict.get(item.menu_item_id)
                if not db_item:
                    raise ValueError(f"Sepetteki ürün bulunamadı veya silinmiş: {item.name}")
                
                if db_item.status != "active":
                    raise ValueError(f"Sipariş edilemeyen pasif ürün: {item.name}")

                if not db_item.price or db_item.price <= 0:
                    raise ValueError(f"Geçerli fiyatı bulunmayan ürün: {item.name}")

                if not db_item.station_code:
                    raise ValueError(f"İstasyon yönlendirmesi eksik olan ürün: {item.name}")

                # Güvenilir fiyat ve istasyon rotasını ez
                item.price = db_item.price
                item.station_code = db_item.station_code
                item.name = db_item.name
                
                total_amount += item.price * item.quantity
                validated_items.append(item)

            # 5. Aktif Bir Adisyon (BillSession) Var mı Sorgula, Yoksa Atomik Olarak Oluştur
            bill_session = BillSessionRepository.get_active_by_table(session, cust_session.table_id)
            if not bill_session:
                bill_session = BillSession(
                    table_id=cust_session.table_id,
                    status="open"
                )
                BillSessionRepository.add(session, bill_session)
                session.flush() # ID edinmek için veriyi yolla

            # 6. PostgreSQL Sipariş (Order) ve Sipariş Kalemi (OrderItem) Kaydı Oluştur
            order_number = f"ORD-{secrets.token_hex(4).upper()}"
            order = Order(
                bill_session_id=bill_session.id,
                order_number=order_number,
                status="submitted",
                total_amount=total_amount,
                currency="TRY"
            )
            OrderRepository.add(session, order)
            session.flush()

            for item in validated_items:
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=uuid.UUID(item.menu_item_id),
                    name=item.name,
                    price=item.price,
                    quantity=item.quantity,
                    note=item.note
                )
                session.add(order_item)

            # 7. İstasyon Yönlendirme Biletlerini (StationTicket) Oluştur
            # İstasyon koduna göre sepet kalemlerini grupla
            station_groups = {}
            for item in validated_items:
                station_groups.setdefault(item.station_code, []).append(item)

            for station_code, items in station_groups.items():
                ticket = StationTicket(
                    order_id=order.id,
                    station_code=station_code,
                    status="pending"
                )
                session.add(ticket)
                session.flush()

                for item in items:
                    ticket_item = StationTicketItem(
                        station_ticket_id=ticket.id,
                        menu_item_id=uuid.UUID(item.menu_item_id),
                        name=item.name,
                        quantity=item.quantity,
                        note=item.note
                    )
                    session.add(ticket_item)

            # 8. Müşteri Oturumunu Anında Çevrimdışı (Offline) Yap
            cust_session.status = "offline"
            session.add(cust_session)

            # 9. Veritabanı İşlemlerini Kaydet
            session.commit()

            # 10. Redis Sepetini Temizle (Clear Cart)
            # PostgreSQL commit'i bittikten sonra sepeti siliyoruz
            RedisCartRepository.clear_cart(tenant_slug, table_id_str)

            session.refresh(order)
            # Pre-load lazy relationships inside active transaction boundary
            _ = order.items
            _ = order.station_tickets
            for ticket in order.station_tickets:
                _ = ticket.items
            session.expunge(order)
            return order

    @staticmethod
    def get_current_bill_summary(tenant_slug: str, session_id: uuid.UUID) -> dict:
        """Returns the current open bill details for the table linked to the active session."""
        with session_manager.tenant_session(tenant_slug) as session:
            cust_session = CustomerSessionRepository.get_by_id(session, session_id)
            if not cust_session:
                raise ValueError("Oturum bulunamadı.")
            
            # Oturum active olmalıdır
            if cust_session.status != "active":
                raise ValueError("Adisyon görüntülemek için aktif oturum gereklidir.")

            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            if cust_session.expires_at_utc <= now:
                cust_session.status = "expired"
                session.add(cust_session)
                session.commit()
                raise ValueError("Oturum süresi dolmuş.")

            bill = BillSessionRepository.get_active_by_table(session, cust_session.table_id)
            if not bill:
                return {
                    "bill_session_id": None,
                    "status": "closed",
                    "total_amount": 0.00,
                    "orders": []
                }

            # Bu adisyona ait siparişleri ve kalemleri topla
            orders = OrderRepository.list_by_bill_session(session, bill.id)
            bill_orders = []
            bill_total = Decimal("0.00")

            for ord in orders:
                if ord.status == "voided":
                    continue
                bill_total += ord.total_amount
                
                order_items = []
                for item in ord.items:
                    order_items.append({
                        "menu_item_id": str(item.menu_item_id),
                        "name": item.name,
                        "price": float(item.price),
                        "quantity": item.quantity,
                        "note": item.note
                    })

                bill_orders.append({
                    "order_id": str(ord.id),
                    "order_number": ord.order_number,
                    "status": ord.status,
                    "total_amount": float(ord.total_amount),
                    "submitted_at_utc": ord.submitted_at_utc.isoformat(),
                    "items": order_items
                })

            return {
                "bill_session_id": str(bill.id),
                "status": bill.status,
                "total_amount": float(bill_total),
                "orders": bill_orders
            }

    @staticmethod
    def get_bill_session_detail(tenant_slug: str, bill_session_id: uuid.UUID) -> BillSession:
        with session_manager.tenant_session(tenant_slug) as session:
            bill = BillSessionRepository.get_by_id(session, bill_session_id)
            if not bill:
                raise ValueError("Adisyon bulunamadı.")
            
            # Preload relationships within active transaction boundary
            _ = bill.orders
            _ = bill.manual_payments
            _ = bill.reopen_events
            for ord in bill.orders:
                _ = ord.items
                _ = ord.station_tickets
                for t in ord.station_tickets:
                    _ = t.items
            session.expunge(bill)
            return bill

    @staticmethod
    def record_manual_payment(
        tenant_slug: str,
        bill_session_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        payment_method: str,
        external_reference: Optional[str] = None,
        note: Optional[str] = None
    ) -> ManualPayment:
        if amount <= 0:
            raise ValueError("Ödeme tutarı sıfırdan büyük olmalıdır.")
        
        with session_manager.tenant_session(tenant_slug) as session:
            # Lock for update to prevent concurrent race conditions
            bill = BillSessionRepository.get_by_id_for_update(session, bill_session_id)
            if not bill:
                raise ValueError("Adisyon bulunamadı.")
            
            if bill.status not in ("open", "reopened"):
                raise ValueError(f"Sadece açık veya geri açılmış adisyonlara ödeme girilebilir. Durum: {bill.status}")
            
            # Recalculate unpaid balance
            orders = OrderRepository.list_by_bill_session(session, bill.id)
            bill_total = Decimal("0.00")
            for ord in orders:
                if ord.status != "voided":
                    bill_total += ord.total_amount
            
            recorded_payments = ManualPaymentRepository.list_by_bill_session(session, bill.id)
            total_recorded = sum(p.amount for p in recorded_payments)
            
            unpaid_balance = bill_total - total_recorded
            
            # Initial version constraint: no partial payments or overpayments
            if amount != unpaid_balance:
                raise ValueError("Birebir eşleşmeyen ödeme tutarı. İlk versiyonda parçalı ödeme veya fazla ödeme yapılabilmesi yasaktır.")
            
            payment = ManualPayment(
                bill_session_id=bill.id,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                status="completed",
                external_reference=external_reference,
                note=note
            )
            ManualPaymentRepository.add(session, payment)
            session.commit()
            
            session.refresh(payment)
            session.expunge(payment)
            return payment

    @staticmethod
    def close_bill_session(
        tenant_slug: str,
        bill_session_id: uuid.UUID,
        manual_payment_payload: Optional[dict] = None,
        reason: Optional[str] = None
    ) -> BillSession:
        with session_manager.tenant_session(tenant_slug) as session:
            # Lock for update
            bill = BillSessionRepository.get_by_id_for_update(session, bill_session_id)
            if not bill:
                raise ValueError("Adisyon bulunamadı.")
            
            if bill.status == "closed":
                # Idempotent success
                session.refresh(bill)
                _ = bill.orders
                _ = bill.manual_payments
                _ = bill.reopen_events
                session.expunge(bill)
                return bill
            
            if bill.status not in ("open", "reopened"):
                raise ValueError(f"Sadece açık veya geri açılmış adisyonlar kapatılabilir. Durum: {bill.status}")
            
            # Recalculate total
            orders = OrderRepository.list_by_bill_session(session, bill.id)
            bill_total = Decimal("0.00")
            for ord in orders:
                if ord.status != "voided":
                    bill_total += ord.total_amount
            
            recorded_payments = ManualPaymentRepository.list_by_bill_session(session, bill.id)
            total_recorded = sum(p.amount for p in recorded_payments)
            
            # If payment payload is provided atomically during close
            if manual_payment_payload:
                pay_amount = Decimal(str(manual_payment_payload["amount"]))
                if pay_amount <= 0:
                    raise ValueError("Ödeme tutarı sıfırdan büyük olmalıdır.")
                
                unpaid_balance = bill_total - total_recorded
                if pay_amount != unpaid_balance:
                    raise ValueError("Birebir eşleşmeyen ödeme tutarı. İlk versiyonda parçalı ödeme veya fazla ödeme yapılabilmesi yasaktır.")
                
                payment = ManualPayment(
                    bill_session_id=bill.id,
                    amount=pay_amount,
                    currency=manual_payment_payload.get("currency", "TRY"),
                    payment_method=manual_payment_payload["payment_method"],
                    status="completed",
                    external_reference=manual_payment_payload.get("external_reference"),
                    note=manual_payment_payload.get("note")
                )
                ManualPaymentRepository.add(session, payment)
                total_recorded += pay_amount
            
            # Check exactly matching payments
            if total_recorded != bill_total:
                raise ValueError(f"Adisyon tutarı (₺{bill_total}) ile toplam ödeme tutarı (₺{total_recorded}) eşleşmelidir.")
            
            # Transition status
            bill.status = "closed"
            session.add(bill)
            session.commit()
            
            session.refresh(bill)
            _ = bill.orders
            _ = bill.manual_payments
            _ = bill.reopen_events
            for ord in bill.orders:
                _ = ord.items
            session.expunge(bill)
            return bill

    @staticmethod
    def reopen_bill_session(
        tenant_slug: str,
        bill_session_id: uuid.UUID,
        reason: str,
        reopened_by: str = "staff"
    ) -> BillSession:
        if not reason or not reason.strip():
            raise ValueError("Adisyonu geri açmak için geçerli bir gerekçe girilmelidir.")
        
        with session_manager.tenant_session(tenant_slug) as session:
            bill = BillSessionRepository.get_by_id_for_update(session, bill_session_id)
            if not bill:
                raise ValueError("Adisyon bulunamadı.")
            
            if bill.status in ("open", "reopened"):
                # Idempotent success
                session.refresh(bill)
                _ = bill.orders
                _ = bill.manual_payments
                _ = bill.reopen_events
                session.expunge(bill)
                return bill
            
            if bill.status != "closed":
                raise ValueError(f"Sadece kapatılmış adisyonlar geri açılabilir. Durum: {bill.status}")
            
            # Check active bill session constraint for the table
            active_bill = BillSessionRepository.get_active_by_table(session, bill.table_id)
            if active_bill:
                raise ValueError("Bu masa için zaten açık veya aktif bir adisyon oturumu bulunmaktadır.")
            
            # Create reopen log event record
            event = BillReopenEvent(
                bill_session_id=bill.id,
                reason=reason,
                reopened_by=reopened_by
            )
            BillReopenEventRepository.add(session, event)
            
            # Transition status back to active (represented as 'open')
            bill.status = "open"
            session.add(bill)
            session.commit()
            
            session.refresh(bill)
            _ = bill.orders
            _ = bill.manual_payments
            _ = bill.reopen_events
            for ord in bill.orders:
                _ = ord.items
            session.expunge(bill)
            return bill
