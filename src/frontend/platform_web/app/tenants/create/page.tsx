"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function CreateTenant() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states matching CreateTenantRequest schema
  const [tenantDisplayName, setTenantDisplayName] = useState("");
  const [tenantSlug, setTenantSlug] = useState("");
  const [tenantOwnerFullName, setTenantOwnerFullName] = useState("");
  const [tenantOwnerEmail, setTenantOwnerEmail] = useState("");
  const [businessType, setBusinessType] = useState("restaurant");
  const [defaultLocale, setDefaultLocale] = useState("tr-TR");
  const [defaultCurrency, setDefaultCurrency] = useState("TRY");
  const [timezone, setTimezone] = useState("Europe/Istanbul");
  const [initialPlan, setInitialPlan] = useState("pro");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Mock API call to simulate provisioning launch
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      setSuccess(true);
      setTimeout(() => {
        router.push("/tenants");
      }, 2000);
    } catch (err: any) {
      setError("Kurulum başlatılamadı. Lütfen alanları kontrol edin.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 flex flex-col flex-1">
      {/* Wizard Header */}
      <div className="pb-5 border-b border-card-border">
        <h1 className="text-2xl font-bold tracking-tight">Yeni Kiracı Kurulum Sihirbazı</h1>
        <p className="text-muted text-sm mt-1">
          Yeni restoran veya cafe işletmesini kaydederek dynamic database provisioning (Celery) sürecini başlatın.
        </p>
      </div>

      {success && (
        <div className="p-4 rounded-lg bg-success/10 border border-success/30 text-success text-sm font-semibold">
          ✓ Kiracı başarıyla oluşturuldu ve veritabanı kurulum işi Celery kuyruğuna alındı! Yönlendiriliyorsunuz...
        </div>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-error/10 border border-error/30 text-error text-sm font-semibold">
          ⚠ Hata: {error}
        </div>
      )}

      {/* Form Content */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm space-y-6">
          <h2 className="text-lg font-bold border-b border-card-border pb-3">1. İşletme ve Domain Bilgileri</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted uppercase">İşletme Adı</label>
              <input
                type="text"
                required
                placeholder="Ör. Boğaz Manzaralı Restoran"
                value={tenantDisplayName}
                onChange={(e) => setTenantDisplayName(e.target.value)}
                className="w-full h-10 rounded-lg border border-card-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted uppercase">Alt Alan Adı (Subdomain Slug)</label>
              <div className="flex h-10 rounded-lg border border-card-border bg-background overflow-hidden focus-within:ring-1 focus-within:ring-primary">
                <input
                  type="text"
                  required
                  placeholder="bogaz-bistro"
                  value={tenantSlug}
                  onChange={(e) => setTenantSlug(e.target.value)}
                  className="flex-1 bg-transparent px-3 text-sm focus:outline-none"
                />
                <span className="bg-card-border/30 px-3 flex items-center text-xs text-muted border-l border-card-border">
                  .iotables.net
                </span>
              </div>
              <p className="text-[10px] text-muted leading-relaxed">
                Slug değeri küçük harfler ve tire (-) içerebilir, platform genelinde benzersiz olmalıdır.
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm space-y-6">
          <h2 className="text-lg font-bold border-b border-card-border pb-3">2. Sahip (Owner) Bilgileri</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted uppercase">Sahibinin Adı Soyadı</label>
              <input
                type="text"
                required
                placeholder="Ör. Ahmet Yılmaz"
                value={tenantOwnerFullName}
                onChange={(e) => setTenantOwnerFullName(e.target.value)}
                className="w-full h-10 rounded-lg border border-card-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted uppercase">Sahibinin E-posta Adresi</label>
              <input
                type="email"
                required
                placeholder="ahmet.yilmaz@bistro.com"
                value={tenantOwnerEmail}
                onChange={(e) => setTenantOwnerEmail(e.target.value)}
                className="w-full h-10 rounded-lg border border-card-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm space-y-6">
          <h2 className="text-lg font-bold border-b border-card-border pb-3">3. Operasyonel Ayarlar & Plan</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted uppercase">İşletme Türü</label>
              <select
                value={businessType}
                onChange={(e) => setBusinessType(e.target.value)}
                className="w-full h-10 rounded-lg border border-card-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="restaurant">Restoran</option>
                <option value="cafe">Cafe / Kahve Evi</option>
                <option value="fast_food">Fast Food</option>
                <option value="pub">Pub / Bar</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted uppercase">Para Birimi</label>
              <select
                value={defaultCurrency}
                onChange={(e) => setDefaultCurrency(e.target.value)}
                className="w-full h-10 rounded-lg border border-card-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="TRY">Türk Lirası (TRY)</option>
                <option value="USD">Amerikan Doları (USD)</option>
                <option value="EUR">Euro (EUR)</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted uppercase">Abonelik Planı</label>
              <select
                value={initialPlan}
                onChange={(e) => setInitialPlan(e.target.value)}
                className="w-full h-10 rounded-lg border border-card-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="standard">Standard Plan</option>
                <option value="pro">Profesyonel Plan</option>
                <option value="enterprise">Kurumsal (Enterprise)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3 pt-4">
          <Link
            href="/tenants"
            className="inline-flex items-center justify-center rounded-lg border border-card-border px-4 py-2 text-sm font-semibold text-muted hover:bg-card-bg transition-colors"
          >
            İptal
          </Link>
          <button
            type="submit"
            disabled={loading || success}
            className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-background hover:bg-primary-hover disabled:opacity-50 transition-colors"
          >
            {loading ? "Kuruluyor..." : "✓ Kurulumu Başlat"}
          </button>
        </div>
      </form>
    </div>
  );
}
