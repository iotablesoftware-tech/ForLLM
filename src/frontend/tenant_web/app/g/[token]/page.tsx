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

  // View States
  const [activeTab, setActiveTab] = useState<"menu" | "contact">("menu");
  
  // Data States
  const [menuItems, setMenuItems] = useState<MenuItemType[]>([]);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [cartVersion, setCartVersion] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Interaction States
  const [notification, setNotification] = useState<string | null>(null);
  const [zoomImage, setZoomImage] = useState<{ name: string; imgSrc: string } | null>(null);
  const [cartOpen, setCartOpen] = useState<boolean>(false);
  const [copiedWifi, setCopiedWifi] = useState<boolean>(false);

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
      setCartOpen(false);
    } catch (err: any) {
      setNotification(`Hata: ${err.message}`);
    }
  };

  const copyWifiPassword = () => {
    navigator.clipboard.writeText("moda12345");
    setCopiedWifi(true);
    setNotification("Wifi şifresi kopyalandı!");
    setTimeout(() => setCopiedWifi(false), 3000);
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-[200] bg-[#111111] flex flex-col items-center justify-center space-y-4 text-center">
        <span className="h-10 w-10 rounded-full border-4 border-[#c9a84c] border-t-transparent animate-spin" />
        <p className="text-[#a09070] text-sm font-semibold tracking-wider uppercase font-sans">Moda Cafe Yükleniyor...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 z-[200] bg-[#111111] flex flex-col items-center justify-center p-6 text-center space-y-4">
        <div className="h-12 w-12 rounded-full bg-[#ef4444]/10 text-[#ef4444] border border-[#ef4444]/20 flex items-center justify-center text-xl font-bold">
          !
        </div>
        <h2 className="text-xl font-playfair font-bold text-[#c9a84c]">Bağlantı Hatası</h2>
        <p className="text-[#a09070] text-xs max-w-xs">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-2.5 bg-[#c9a84c] hover:bg-[#a07832] text-[#111111] rounded-lg font-bold text-xs uppercase tracking-wider transition-colors"
        >
          Tekrar Dene
        </button>
      </div>
    );
  }

  const cartTotal = cartItems.reduce((acc, item) => acc + item.price * item.quantity, 0);
  const cartQuantity = cartItems.reduce((acc, item) => acc + item.quantity, 0);

  return (
    <div className="fixed inset-0 z-[200] bg-[#0c0c0c] overflow-y-auto flex justify-center scrollbar-none select-none">
      {/* 100% Mobile Only Sleek Frame Viewport (max-w-md centered) */}
      <div className="w-full max-w-md min-h-screen bg-[#111111] border-x border-[#222222] shadow-2xl flex flex-col relative text-[#e8e0d0] pb-28">
        
        {/* Sticky Mobile Nav Bar (Moda Cafe Style) */}
        <nav className="sticky top-0 z-50 bg-[#111111]/95 backdrop-blur-md border-b border-[#2e2e2e] px-4 py-3 flex items-center justify-between shadow-md">
          {/* Logo & Brand */}
          <div className="flex items-center gap-2.5 cursor-pointer">
            <div className="h-9 w-9 rounded-full overflow-hidden bg-[#1a1a1a] border border-[#c9a84c]/20 shadow-md">
              <img 
                src="https://karekodrestaurantmenu.com/Pictures/3491c160-2b23-4e12-8ac8-5e0ab98eb5d2.png" 
                alt="Moda Cafe"
                className="h-full w-full object-cover"
                onError={(e) => { e.currentTarget.style.display = "none"; }}
              />
            </div>
            <span className="font-playfair font-extrabold text-sm tracking-wide text-[#c9a84c]">Moda Cafe</span>
          </div>

          {/* Navigation Links */}
          <div className="flex gap-1 bg-[#1a1a1a] border border-[#2e2e2e] p-0.5 rounded-lg">
            <button
              onClick={() => setActiveTab("menu")}
              className={`px-3 py-1.5 rounded-md text-[11px] font-bold tracking-wide transition-all uppercase ${
                activeTab === "menu" 
                  ? "bg-[#c9a84c] text-[#111111]" 
                  : "text-[#a09070] hover:text-[#e8e0d0]"
              }`}
            >
              Menü
            </button>
            <button
              onClick={() => setActiveTab("contact")}
              className={`px-3 py-1.5 rounded-md text-[11px] font-bold tracking-wide transition-all uppercase ${
                activeTab === "contact" 
                  ? "bg-[#c9a84c] text-[#111111]" 
                  : "text-[#a09070] hover:text-[#e8e0d0]"
              }`}
            >
              Wifi
            </button>
          </div>
        </nav>

        {/* Dynamic Live Notification Toast */}
        {notification && (
          <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[300] max-w-xs w-[90%] rounded-xl bg-[#1a1a1a] border border-[#c9a84c]/40 px-4 py-3 shadow-2xl flex items-center justify-center gap-2.5 animate-bounce">
            <span className="h-1.5 w-1.5 rounded-full bg-[#c9a84c] animate-ping shrink-0" />
            <p className="text-[11px] font-bold text-[#e8e0d0] text-center">{notification}</p>
          </div>
        )}

        {/* ─── TAB 1: MENU CATALOG ─── */}
        {activeTab === "menu" && (
          <div className="space-y-6 pt-4">
            {/* Top Brand Logo Banner */}
            <div className="flex justify-center py-2">
              <img 
                src="https://karekodrestaurantmenu.com/Pictures/3491c160-2b23-4e12-8ac8-5e0ab98eb5d2.png" 
                alt="Moda Cafe Banner"
                className="max-h-24 object-contain filter drop-shadow(0 4px 12px rgba(201,168,76,.15))"
                onError={(e) => { e.currentTarget.style.display = "none"; }}
              />
            </div>
            
            <MenuCatalog 
              items={menuItems} 
              onAddToCart={handleAddToCart}
              onZoomImage={(name, imgSrc) => setZoomImage({ name, imgSrc })}
            />
          </div>
        )}

        {/* ─── TAB 2: CONTACT & WIFI ─── */}
        {activeTab === "contact" && (
          <div className="px-6 py-8 flex flex-col items-center text-center space-y-6 animate-item visible">
            {/* Logo */}
            <img 
              src="https://karekodrestaurantmenu.com/Pictures/3491c160-2b23-4e12-8ac8-5e0ab98eb5d2.png" 
              alt="Moda Cafe"
              className="max-h-24 object-contain filter drop-shadow(0 4px 12px rgba(201,168,76,.15))"
            />
            
            <h2 className="font-playfair text-xl font-bold text-[#c9a84c]">İletişim & Sosyal Ağlar</h2>
            
            {/* Contact Details Card */}
            <div className="w-full bg-[#1a1a1a] border border-[#2e2e2e] rounded-xl p-5 space-y-4 text-left shadow-lg">
              <div className="flex items-start gap-3 text-xs">
                <span className="text-base">📍</span>
                <span className="text-[#e8e0d0] leading-relaxed">Cumhuriyet Mahallesi İnönü Caddesi No:21 Şarköy/Tekirdağ</span>
              </div>
              <div className="flex items-start gap-3 text-xs border-t border-[#2e2e2e]/50 pt-3">
                <span className="text-base">📞</span>
                <a href="tel:05377623108" className="text-[#c9a84c] hover:underline font-bold">0537 762 31 08</a>
              </div>
            </div>

            {/* Wifi Details Card (Premium addition) */}
            <h2 className="font-playfair text-xl font-bold text-[#c9a84c] pt-2">Masa Wifi Bağlantısı</h2>
            <div className="w-full bg-[#1a1a1a] border border-[#2e2e2e] rounded-xl p-5 space-y-4 text-left shadow-lg">
              <div className="flex justify-between items-center text-xs">
                <span className="text-[#a09070] font-bold uppercase tracking-wider text-[10px]">Ağ Adı (SSID):</span>
                <span className="font-bold text-[#e8e0d0]">Moda Cafe Lounge</span>
              </div>
              <div className="flex justify-between items-center text-xs border-t border-[#2e2e2e]/50 pt-3">
                <div className="space-y-0.5">
                  <span className="text-[#a09070] font-bold uppercase tracking-wider text-[10px] block">Şifre:</span>
                  <span className="font-bold text-[#e8e0d0] font-mono">moda12345</span>
                </div>
                <button
                  onClick={copyWifiPassword}
                  className="px-3 py-1.5 bg-[#c9a84c]/10 border border-[#c9a84c]/20 rounded-lg text-[#c9a84c] text-[10px] font-bold hover:bg-[#c9a84c] hover:text-[#111111] transition-all"
                >
                  {copiedWifi ? "Kopyalandı ✓" : "Şifreyi Kopyala"}
                </button>
              </div>
            </div>

            {/* Instagram Link (Premium Custom Gradient) */}
            <div className="w-full pt-4 space-y-2">
              <p className="text-[10px] font-bold uppercase tracking-wider text-[#a09070]">Bizi Sosyal Ağlardan Takip Edin</p>
              <a 
                href="https://www.instagram.com/modaloungesarkoy/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-r from-[#f09433] via-[#dc2743] to-[#bc1888] text-white font-bold text-xs uppercase tracking-wider shadow-lg hover:scale-105 active:scale-95 transition-all"
              >
                <span>📷</span>
                <span>Instagram'da Keşfet</span>
              </a>
            </div>
          </div>
        )}

        {/* ─── STICKY BOTTOM COLLABORATIVE CART BAR ─── */}
        {cartQuantity > 0 && !cartOpen && (
          <div 
            onClick={() => setCartOpen(true)}
            className="fixed bottom-0 left-1/2 -translate-x-1/2 max-w-md w-full z-[240] bg-[#1a1a1a]/95 backdrop-blur-md border-t border-[#2e2e2e] p-4 flex items-center justify-between shadow-2xl cursor-pointer hover:bg-[#222222] transition-colors"
          >
            {/* Left Info: Cart Item Count and Connected Avatars */}
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-[#c9a84c]/10 border border-[#c9a84c]/30 flex items-center justify-center font-bold text-[#c9a84c] relative">
                🛒
                <span className="absolute -top-1.5 -right-1.5 h-5 w-5 rounded-full bg-[#c9a84c] text-[#111111] font-extrabold text-[10px] flex items-center justify-center border border-[#1a1a1a]">
                  {cartQuantity}
                </span>
              </div>
              <div className="space-y-0.5">
                <span className="text-xs font-bold text-[#e8e0d0] block">Masadaki Sepet</span>
                {/* Avatars */}
                <div className="flex items-center gap-1.5">
                  <div className="flex -space-x-1">
                    <div className="h-4 w-4 rounded-full bg-orange-500 border border-[#1a1a1a] flex items-center justify-center text-[7px] font-bold text-white">Siz</div>
                    <div className="h-4 w-4 rounded-full bg-emerald-500 border border-[#1a1a1a] flex items-center justify-center text-[7px] font-bold text-white">AH</div>
                  </div>
                  <span className="text-[8px] text-[#a09070] font-semibold">2 kişi ekleme yaptı</span>
                </div>
              </div>
            </div>

            {/* Right: Total & Slide Indicator */}
            <div className="flex items-center gap-3">
              <div className="text-right">
                <span className="text-[9px] text-[#a09070] block uppercase font-bold tracking-wide">Toplam Tutar:</span>
                <span className="font-playfair font-bold text-sm text-[#c9a84c]">₺{cartTotal}</span>
              </div>
              <span className="text-xs text-[#c9a84c] animate-bounce">▲</span>
            </div>
          </div>
        )}

        {/* ─── SLIDING BOTTOM DRAWER / COLLABORATIVE CART SHEET ─── */}
        {cartOpen && (
          <div className="fixed inset-0 z-[250] bg-black/75 flex justify-center items-end" onClick={() => setCartOpen(false)}>
            <div 
              className="w-full max-w-md bg-[#1a1a1a] rounded-t-2xl shadow-2xl transition-all duration-300 transform translate-y-0 border-t border-[#2e2e2e]"
              onClick={(e) => e.stopPropagation()}
            >
              <CollaborativeCart
                items={cartItems}
                onRemove={handleRemoveItem}
                onClear={handleClearCart}
                onSubmitOrder={handleSubmitOrder}
                onClose={() => setCartOpen(false)}
              />
            </div>
          </div>
        )}

        {/* ─── IMAGE ZOOM MODAL DIALOG ─── */}
        {zoomImage && (
          <div 
            onClick={() => setZoomImage(null)}
            className="fixed inset-0 z-[350] bg-black/90 flex flex-col items-center justify-center p-6 cursor-zoom-out animate-item visible"
          >
            {/* Close Button */}
            <button 
              onClick={() => setZoomImage(null)}
              className="absolute top-6 right-6 text-[#a09070] hover:text-white bg-[#222222]/80 border border-[#2e2e2e] h-8 w-8 rounded-full flex items-center justify-center font-bold text-xs"
            >
              ✕
            </button>
            <div className="max-w-sm w-full bg-[#1a1a1a] border border-[#2e2e2e] rounded-2xl overflow-hidden shadow-2xl" onClick={(e) => e.stopPropagation()}>
              <img 
                src={zoomImage.imgSrc} 
                alt={zoomImage.name} 
                className="w-full aspect-square object-cover"
              />
              <div className="p-5 space-y-2">
                <h3 className="font-playfair font-bold text-lg text-[#c9a84c]">{zoomImage.name}</h3>
                <p className="text-xs text-[#a09070] leading-relaxed">Özel el yapımı premium hazırlık. Tamamen taze ve leziz içerikler ile masanıza sunulur.</p>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
