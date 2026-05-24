import json
import uuid
from typing import Optional
from decimal import Decimal
from app.core.infrastructure import redis_client
from app.modules.Cart.domain.models import Cart, CartItem

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)  # float format is safe for prices in JSON representation
        return super().default(o)

class RedisCartRepository:
    @staticmethod
    def _get_key(tenant_slug: str, table_id: str) -> str:
        return f"iotable:tenant:{tenant_slug}:table:{table_id}:cart"

    @classmethod
    def get_cart(cls, tenant_slug: str, table_id: str) -> Cart:
        key = cls._get_key(tenant_slug, table_id)
        data = redis_client.get(key)
        if not data:
            # Sepet henüz oluşturulmamışsa boş bir sepet dön
            return Cart(cart_version=1, items={})
        
        try:
            cart_dict = json.loads(data)
            return Cart.model_validate(cart_dict)
        except Exception:
            return Cart(cart_version=1, items={})

    @classmethod
    def save_cart(cls, tenant_slug: str, table_id: str, cart: Cart, expected_version: int) -> Cart:
        key = cls._get_key(tenant_slug, table_id)
        
        # 1. Optimistic Locking Sürüm Doğrulaması
        current_cart = cls.get_cart(tenant_slug, table_id)
        if current_cart.cart_version != expected_version:
            raise ValueError("CART_STATE_OUTOFDATE")

        # 2. Sepet Toplam Tutarını Sunucu Tarafında Baştan Hesapla
        total = Decimal("0.00")
        for item in cart.items.values():
            total += item.price * item.quantity
        cart.total_amount = total

        # 3. Sürüm Numarasını Arttır
        cart.cart_version = current_cart.cart_version + 1

        # 4. Redis'e Kaydet
        cart_data = json.dumps(cart.model_dump(), cls=DecimalEncoder)
        redis_client.set(key, cart_data)
        
        return cart

    @classmethod
    def clear_cart(cls, tenant_slug: str, table_id: str) -> None:
        key = cls._get_key(tenant_slug, table_id)
        # Sepeti sıfırla (sürüm 1'e döner, items boşalır)
        empty_cart = Cart(cart_version=1, items={})
        redis_client.set(key, json.dumps(empty_cart.model_dump(), cls=DecimalEncoder))
