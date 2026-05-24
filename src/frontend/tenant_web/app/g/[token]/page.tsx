"use client";

import { useState, use, useEffect } from "react";
import MenuCatalog, { MenuItemType } from "./_components/MenuCatalog";
import CollaborativeCart from "./_components/CollaborativeCart";
import { joinSessionAction, getMenuAction } from "./_api/sessionActions";
import {
  getCartAction,
  addCartItemAction,
  deleteCartItemAction,
  submitOrderAction,
  Cart,
} from "./_api/cartActions";

interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
  addedBy: string;
  avatarColor: string;
}

interface PageProps {
  params: Promise<{ token: string }>;
}

export default function GuestOrderingPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const guestToken = resolvedParams.token;

  const [menuItems, setMenuItems] = useState<MenuItemType[]>([]);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [cartVersion, setCartVersion] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<string | null>(null);

  // Helper function to sync local state with backend Cart
  const syncCartState = (backendCart: Cart) => {
    setCartVersion(backendCart.cart_version);
    const mappedItems: CartItem[] = Object.values(backendCart.items).map(item => ({
      id: item.menu_item_id,
      name: item.name,
      price: item.price,
      quantity: item.quantity,
      addedBy: item.note || "Masa",
      avatarColor: "bg-orange-500",
    }));
    setCartItems(mappedItems);
  };

  // 1. Join session and load initial data
  useEffect(() => {
    async function initSession() {
      try {
        setLoading(true);
        // Step 1: Join the guest session using the URL QR token
        await joinSessionAction(guestToken);
        
        // Step 2: Fetch the dynamic menu catalog
        const dbMenu = await getMenuAction();
        const mappedMenu: MenuItemType[] = dbMenu.map(item => ({
          id: item.id,
          name: item.name,
          price: item.price,
          category: item.category,
          available: item.status === "active",
        }));
        setMenuItems(mappedMenu);

        // Step 3: Fetch the initial shared cart
        const initialCart = await getCartAction();
        syncCartState(initialCart);
        
        setLoading(false);
      } catch (err: any) {
        console.error("Session initialization failed:", err);
        setError(err.message || "Oturum başlatılamadı. Lütfen QR kodunu tekrar okutun.");
        setLoading(false);
      }
    }
    initSession();
  }, [guestToken]);

  // 2. Poll collaborative cart every 5 seconds to sync other guests' changes
  useEffect(() => {
    if (loading || error) return;

    const interval = setInterval(async () => {
      try {
        const liveCart = await getCartAction();
        if (liveCart.cart_version !== cartVersion) {
          syncCartState(liveCart);
          setNotification("Sepetiniz canlı olarak güncellendi!");
        }
      } catch (err) {
        // Silent catch for background polling
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [loading, error, cartVersion]);

  // Dismiss notification after 4s
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => setNotification(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  const handleAddToCart = async (item: MenuItemType) => {
    try {
      setNotification(`'${item.name}' sepete ekleniyor...`);
      const updatedCart = await addCartItemAction(item.id, 1, cartVersion, "Siz");
      syncCartState(updatedCart);
      setNotification(`'${item.name}' sepetinize başarıyla eklendi.`);
    } catch (err: any) {
      setNotification(`Hata: ${err.message}`);
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    try {
      setNotification("Ürün sepetten çıkarılıyor...");
      const updatedCart = await deleteCartItemAction(itemId, cartVersion);
      syncCartState(updatedCart);
      setNotification("Ürün sepetten başarıyla çıkarıldı.");
    } catch (err: any) {
      setNotification(`Hata: ${err.message}`);
    }
  };

  const handleClearCart = async () => {
    try {
      setNotification("Sepet temizleniyor...");
      let currentVersion = cartVersion;
      for (const item of cartItems) {
        const updatedCart = await deleteCartItemAction(item.id, currentVersion);
        currentVersion = updatedCart.cart_version;
      }
      const finalCart = await getCartAction();
      syncCartState(finalCart);
      setNotification("Sepet başarıyla temizlendi.");
    } catch (err: any) {
      setNotification(`Hata: ${err.message}`);
    }
  };

  const handleSubmitOrder = async () => {
    try {
      setNotification("Siparişiniz mutfağa iletiliyor...");
      const response = await submitOrderAction(cartVersion, "Masa siparişi gönderildi");
      setNotification(`Siparişiniz başarıyla iletildi! Sipariş No: ${response.order_number}`);
      setCartItems([]);
      setCartVersion(1);
    } catch (err: any) {
      setNotification(`Hata: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-12 space-y-4 bg-background">
        <span className="h-10 w-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
        <p className="text-muted text-sm font-semibold">Oturum kuruluyor ve menü yükleniyor...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 py-12 space-y-4 max-w-md mx-auto text-center bg-background">
        <div className="h-12 w-12 rounded-full bg-error/10 text-error flex items-center justify-center text-xl font-bold">
          !
        </div>
        <h2 className="text-xl font-bold">Bağlantı Hatası</h2>
        <p className="text-muted text-sm">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-primary text-background rounded-lg font-bold text-sm"
        >
          Tekrar Dene
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 flex flex-col flex-1 relative bg-background">
      {/* Live Collaborative Notification Toast */}
      {notification && (
        <div className="fixed bottom-5 right-5 z-50 rounded-xl bg-card-bg border border-accent/40 px-5 py-4 shadow-xl flex items-center gap-3 animate-bounce">
          <span className="h-2.5 w-2.5 rounded-full bg-accent animate-ping" />
          <p className="text-sm font-semibold text-foreground">{notification}</p>
        </div>
      )}

      {/* Header Info */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-6 border-b border-card-border">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-primary px-2 py-0.5 rounded bg-primary/10">
            Masa QR Sipariş Sistemi
          </span>
          <h1 className="text-3xl font-extrabold tracking-tight mt-2">Bistro Ankara - Masa 12</h1>
          <p className="text-muted text-sm mt-1">
            Yemeklerinizi sepete ekleyin, masadaki herkesle aynı anda sepetinizi güncelleyin.
          </p>
        </div>
        
        <div className="flex items-center gap-3 text-xs bg-card-bg border border-card-border px-4 py-2 rounded-xl">
          <span className="text-muted font-medium">Bağlantı Token:</span>
          <code className="bg-primary/5 text-primary font-bold font-mono px-1.5 py-0.5 rounded border border-primary/20">
            {guestToken.slice(0, 12)}...
          </code>
        </div>
      </div>

      {/* Two Column Layout: Menu on left, Collaborative Cart on right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-xl font-bold tracking-tight">Menü Kataloğu</h2>
          <MenuCatalog items={menuItems} onAddToCart={handleAddToCart} />
        </div>
        
        <div className="lg:col-span-1">
          <CollaborativeCart 
            items={cartItems} 
            onRemove={handleRemoveItem} 
            onClear={handleClearCart}
            onSubmitOrder={handleSubmitOrder}
          />
        </div>
      </div>
    </div>
  );
}
