import uuid
import datetime
import secrets
import json
from typing import Optional
from sqlalchemy.orm import Session
from app.core.infrastructure import session_manager, redis_client
from app.modules.Tables.domain.models import Table
from app.modules.CustomerAccess.domain.models import CustomerSession
from app.modules.CustomerAccess.infrastructure.persistence import CustomerSessionRepository

class CustomerAccessService:
    @staticmethod
    def join_session(tenant_slug: str, qr_token: str) -> CustomerSession:
        if not tenant_slug or not qr_token:
            raise ValueError("Tenant slug ve QR token zorunludur.")

        with session_manager.tenant_session(tenant_slug) as session:
            # 1. QR Token ile Masayı Ara
            table = session.query(Table).filter(Table.qr_token == qr_token).first()
            if not table:
                raise ValueError("Geçersiz QR kod veya masa bulunamadı.")
            
            if table.status != "active":
                raise ValueError("Masa şu anda aktif değil.")

            # 2. QR Token Süre Kontrolü
            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            if table.qr_expires_at and table.qr_expires_at <= now:
                raise ValueError("QR kodun süresi dolmuş.")

            # 3. QR Token Rotasyonu (Single-use consume)
            # Yeni bir benzersiz QR token üret ve süresini 24 saat uzat
            new_qr_token = f"qr_{secrets.token_hex(16)}"
            table.qr_token = new_qr_token
            table.qr_expires_at = now + datetime.timedelta(hours=24)
            session.add(table)

            # 4. Taze Müşteri Oturumu (CustomerSession) Oluşturma
            expires_at = now + datetime.timedelta(minutes=10)
            max_expires_at = now + datetime.timedelta(minutes=40)
            
            customer_session = CustomerSession(
                tenant_slug=tenant_slug,
                table_id=table.id,
                status="active",
                expires_at_utc=expires_at,
                extension_count=0,
                max_extensions=3,
                max_expires_at_utc=max_expires_at
            )
            CustomerSessionRepository.add(session, customer_session)
            session.commit()

            # 5. Redis Üzerinde Masaya Ait Boş Sepet (Cart) İlklendirme
            # Redis anahtarı: iotable:tenant:{tenantSlug}:table:{tableId}:cart
            cart_key = f"iotable:tenant:{tenant_slug}:table:{table.id}:cart"
            initial_cart = {
                "cart_version": 1,
                "items": {}
            }
            redis_client.set(cart_key, json.dumps(initial_cart))

            # Refresh to load committed fields (like id, created_at)
            session.refresh(customer_session)
            session.expunge(customer_session)
            return customer_session

    @staticmethod
    def extend_session(tenant_slug: str, session_id: uuid.UUID) -> CustomerSession:
        with session_manager.tenant_session(tenant_slug) as session:
            customer_session = CustomerSessionRepository.get_by_id(session, session_id)
            if not customer_session:
                raise ValueError("Oturum bulunamadı.")
            
            if customer_session.status != "active":
                raise ValueError(f"Aktif olmayan bir oturum uzatılamaz. Statü: {customer_session.status}")

            now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            
            # Süre dolmuşsa statüyü güncelliyoruz
            if customer_session.expires_at_utc <= now:
                customer_session.status = "expired"
                session.add(customer_session)
                session.commit()
                raise ValueError("Oturum süresi dolmuş, uzatılamaz.")

            # Limit Kontrolleri
            if customer_session.extension_count >= customer_session.max_extensions:
                raise ValueError("Maksimum oturum uzatma sınırına (3 kez) ulaşıldı.")

            if now >= customer_session.max_expires_at_utc:
                raise ValueError("Maksimum oturum süresine (40 dakika) ulaşıldı.")

            # Oturumu 10 dakika uzat (max_expires_at_utc sınırını aşmayacak şekilde)
            new_expiry = customer_session.expires_at_utc + datetime.timedelta(minutes=10)
            if new_expiry > customer_session.max_expires_at_utc:
                new_expiry = customer_session.max_expires_at_utc

            customer_session.expires_at_utc = new_expiry
            customer_session.extension_count += 1
            session.add(customer_session)
            session.commit()
            
            session.refresh(customer_session)
            session.expunge(customer_session)
            return customer_session

    @staticmethod
    def get_current_session(tenant_slug: str, session_id: uuid.UUID) -> CustomerSession:
        with session_manager.tenant_session(tenant_slug) as session:
            customer_session = CustomerSessionRepository.get_by_id(session, session_id)
            if not customer_session:
                raise ValueError("Oturum bulunamadı.")
            
            if customer_session.status == "active":
                now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                if customer_session.expires_at_utc <= now:
                    customer_session.status = "expired"
                    session.add(customer_session)
                    session.commit()
                    session.refresh(customer_session)
            session.expunge(customer_session)
            return customer_session
