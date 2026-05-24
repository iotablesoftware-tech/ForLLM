from pydantic import BaseModel, Field
from typing import Optional, Dict
from decimal import Decimal

class CartItem(BaseModel):
    menu_item_id: str = Field(..., description="Menü elemanının benzersiz kimliği (UUID).")
    name: str = Field(..., description="Menü elemanının adı.")
    price: Decimal = Field(..., description="Ürünün eklendiği andaki birim fiyatı.")
    quantity: int = Field(..., description="Adet bilgisi. Pozitif tam sayı olmalıdır.")
    note: Optional[str] = Field(None, description="Müşterinin bu ürünle ilgili özel notu.")
    station_code: str = Field(..., description="Ürünün yönlendirileceği mutfak/hazırlık istasyon kodu.")

class Cart(BaseModel):
    items: Dict[str, CartItem] = Field(default_factory=dict, description="Sepetteki ürünler (key olarak menu_item_id kullanılır).")
    cart_version: int = Field(1, description="Sepet sürümü (Optimistic Locking doğrulaması için).")
    total_amount: Decimal = Field(Decimal("0.00"), description="Sepetin toplam tutarı.")
    currency: str = Field("TRY", description="Sepet para birimi.")
