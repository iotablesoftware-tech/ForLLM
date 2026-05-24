"use client";

import { useState } from "react";
import Link from "next/link";

export default function RestaurantConsoleHome() {
  // Settings state (mock toggle state for rich interactive manager experience)
  const [selfOrdering, setSelfOrdering] = useState(true);
  const [stationAcceptance, setStationAcceptance] = useState(true);
  const [notification, setNotification] = useState<string | null>(null);

  const handleToggle = (setting: "self" | "station") => {
    if (setting === "self") {
      setSelfOrdering(!selfOrdering);
      setNotification(`Müşteri Sipariş Sistemi ${!selfOrdering ? "AKTİF" : "DEAKTİF"} edildi.`);
    } else {
      setStationAcceptance(!stationAcceptance);
      setNotification(`Mutfak Sipariş Acknowledgment ${!stationAcceptance ? "ZORUNLU" : "SERBEST"} yapıldı.`);
    }
    setTimeout(() => setNotification(null), 3000);
  };

  return (
    <div className="space-y-8 flex flex-col flex-1 select-none">
      {/* Management Console Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-card-border">
        <div>
          <div className="flex items-center gap-2 text-xs text-muted mb-1">
            <span className="bg-accent/10 text-accent text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
              Yönetim Portalı
            </span>
            <span>•</span>
            <span className="text-muted">Konfigürasyon ve Ayarlar</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">İşletme Yönetim Konsolu</h1>
          <p className="text-muted text-sm mt-1">
            Menü kataloğunu güncelleyin, şube operasyon ayarlarını yönetin ve cihaz/masa durumlarını denetleyin.
          </p>
        </div>

        <Link
          href="/app"
          className="h-10 px-4 rounded-xl bg-primary hover:bg-primary-hover text-background text-xs font-bold transition-colors flex items-center justify-center gap-1.5 shadow-md"
        >
          🖥️ Personel Çalışma Alanı &rarr;
        </Link>
      </div>

      {/* Floating Notification Toast */}
      {notification && (
        <div className="fixed bottom-6 right-6 z-[300] max-w-sm rounded-xl bg-[#162a1c] border border-[#22c55e]/30 text-[#22c55e] px-4 py-3 shadow-2xl flex items-center gap-2.5 animate-bounce">
          <span className="text-sm">✓</span>
          <p className="text-xs font-bold">{notification}</p>
        </div>
      )}

      {/* Configuration Grid Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* Card 1: Menu Catalog CRUD Editor */}
        <div className="bg-card-bg border border-card-border rounded-2xl p-6 flex flex-col justify-between hover:border-accent/40 transition-all shadow-sm">
          <div className="space-y-3">
            <div className="h-10 w-10 rounded-xl bg-[#c9a84c]/10 border border-[#c9a84c]/20 flex items-center justify-center text-xl shadow-md">
              🍔
            </div>
            <h2 className="text-lg font-bold text-foreground">Menü & Ürün Kataloğu</h2>
            <p className="text-xs text-muted leading-relaxed">
              Restoranınızın lezzet kataloğunu yönetin. Kategori ekleyebilir, ürün fiyatlarını güncelleyebilir ve mutfak istasyonu eşleştirmelerini yapabilirsiniz.
            </p>
          </div>
          <div className="pt-6">
            <Link
              href="/console/menu"
              className="w-full h-9 rounded-lg border border-card-border hover:border-accent bg-background hover:bg-accent/5 text-xs font-bold text-accent transition-all flex items-center justify-center gap-1.5"
            >
              Kataloğu Düzenle &rarr;
            </Link>
          </div>
        </div>

        {/* Card 2: QR & Tables Management (Constitutional Placeholder) */}
        <div className="bg-card-bg border border-card-border rounded-2xl p-6 flex flex-col justify-between hover:border-accent/40 transition-all shadow-sm">
          <div className="space-y-3">
            <div className="h-10 w-10 rounded-xl bg-[#c9a84c]/10 border border-[#c9a84c]/20 flex items-center justify-center text-xl shadow-md">
              📍
            </div>
            <h2 className="text-lg font-bold text-foreground">Masa & QR Kod Yönetimi</h2>
            <p className="text-xs text-muted leading-relaxed">
              Fiziki salon planını yönetin. Masalar tanımlayabilir, ESP32 QR display entegrasyonu yapabilir ve basılabilir masa karekod etiket şablonları indirebilirsiniz.
            </p>
          </div>
          <div className="pt-6">
            <button
              onClick={() => alert("Masa ve QR kod yönetim paneli Aşama 8 kapsamında devreye alınacaktır.")}
              className="w-full h-9 rounded-lg border border-card-border hover:border-accent/50 bg-[#1e1e1e] hover:bg-[#222222] text-xs font-bold text-muted transition-all flex items-center justify-center gap-1.5"
            >
              Masaları Yönet &rarr;
            </button>
          </div>
        </div>

        {/* Card 3: Operational Settings & Feature Flags */}
        <div className="bg-card-bg border border-card-border rounded-2xl p-6 flex flex-col justify-between hover:border-accent/40 transition-all shadow-sm">
          <div className="space-y-3">
            <div className="h-10 w-10 rounded-xl bg-[#c9a84c]/10 border border-[#c9a84c]/20 flex items-center justify-center text-xl shadow-md">
              ⚙️
            </div>
            <h2 className="text-lg font-bold text-foreground">Sistem Ayarları</h2>
            <p className="text-xs text-muted leading-relaxed">
              Kiracı veri tabanı düzeyinde self-ordering aktif/pasif durumlarını, mutfak onay ve yazıcı kuyruk ayarlarını doğrudan yönetin.
            </p>
          </div>
          <div className="pt-6">
            <button
              onClick={() => alert("Sistem ayarları özelleştirme paneli Aşama 8 kapsamında devreye alınacaktır.")}
              className="w-full h-9 rounded-lg border border-card-border hover:border-accent/50 bg-[#1e1e1e] hover:bg-[#222222] text-xs font-bold text-muted transition-all flex items-center justify-center gap-1.5"
            >
              Tüm Ayarları Göster &rarr;
            </button>
          </div>
        </div>

      </div>

      {/* Operational Settings Toggles (Rich Interactive Feature) */}
      <div className="bg-card-bg border border-card-border rounded-2xl p-6 shadow-sm space-y-6">
        <h2 className="text-sm font-bold uppercase tracking-wider text-accent border-b border-card-border pb-3">Hızlı Operasyon Parametreleri</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Toggle 1: Self Ordering */}
          <div className="flex items-center justify-between p-4 bg-background/50 border border-card-border rounded-xl">
            <div className="space-y-1 pr-4">
              <span className="text-xs font-bold block">Müşteri Self-Servis Sipariş Sistemi (Self-Ordering)</span>
              <p className="text-[10px] text-muted">Aktif edildiğinde müşteriler QR kod okutarak kendi sepetlerinden sipariş gönderebilirler.</p>
            </div>
            <button
              onClick={() => handleToggle("self")}
              className={`h-7 px-4 rounded-lg text-[10px] font-extrabold tracking-wide transition-all uppercase shrink-0 ${
                selfOrdering 
                  ? "bg-success/15 border border-success/35 text-success" 
                  : "bg-muted/15 border border-card-border text-muted"
              }`}
            >
              {selfOrdering ? "Aktif" : "Deaktif"}
            </button>
          </div>

          {/* Toggle 2: Station Acceptance Required */}
          <div className="flex items-center justify-between p-4 bg-background/50 border border-card-border rounded-xl">
            <div className="space-y-1 pr-4">
              <span className="text-xs font-bold block">Mutfak Sipariş Kabulü (Station Acknowledgment)</span>
              <p className="text-[10px] text-muted">Zorunlu olduğunda mutfak personeli yeni siparişi hazırlamadan önce "Kabul Et" butonuna basmalıdır.</p>
            </div>
            <button
              onClick={() => handleToggle("station")}
              className={`h-7 px-4 rounded-lg text-[10px] font-extrabold tracking-wide transition-all uppercase shrink-0 ${
                stationAcceptance 
                  ? "bg-success/15 border border-success/35 text-success" 
                  : "bg-muted/15 border border-card-border text-muted"
              }`}
            >
              {stationAcceptance ? "Zorunlu" : "Serbest"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
