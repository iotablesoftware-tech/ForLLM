"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

interface TenantDetail {
  id: string;
  displayName: string;
  slug: string;
  domain: string;
  status: "active" | "draft" | "suspended" | "deactivated";
  businessType: string;
  ownerName: string;
  ownerEmail: string;
  defaultCurrency: string;
  defaultLocale: string;
  timezone: string;
  databaseName: string;
  databaseStatus: "healthy" | "migrating" | "error";
  schemaVersion: string;
}

const MOCK_TENANTS: Record<string, TenantDetail> = {
  "1": {
    id: "1",
    displayName: "Ankara Gurme Bistro",
    slug: "bistro-ankara",
    domain: "bistro-ankara.iotables.net",
    status: "active",
    businessType: "restaurant",
    ownerName: "Ahmet Yılmaz",
    ownerEmail: "ahmet@gurmebistro.com",
    defaultCurrency: "TRY",
    defaultLocale: "tr-TR",
    timezone: "Europe/Istanbul",
    databaseName: "iotable_tenant_bistro-ankara",
    databaseStatus: "healthy",
    schemaVersion: "20260524_operational_baseline"
  },
  "2": {
    id: "2",
    displayName: "Piazza Coffee & Bakery",
    slug: "cafe-piazza",
    domain: "cafe-piazza.iotables.net",
    status: "active",
    businessType: "cafe",
    ownerName: "Elif Demir",
    ownerEmail: "elif@piazzacoffee.com",
    defaultCurrency: "TRY",
    defaultLocale: "tr-TR",
    timezone: "Europe/Istanbul",
    databaseName: "iotable_tenant_cafe-piazza",
    databaseStatus: "healthy",
    schemaVersion: "20260524_operational_baseline"
  },
  "3": {
    id: "3",
    displayName: "Burger Island Express",
    slug: "burger-island",
    domain: "burger-island.iotables.net",
    status: "suspended",
    businessType: "fast_food",
    ownerName: "Caner Ege",
    ownerEmail: "caner@burgerisland.com",
    defaultCurrency: "TRY",
    defaultLocale: "tr-TR",
    timezone: "Europe/Istanbul",
    databaseName: "iotable_tenant_burger-island",
    databaseStatus: "error",
    schemaVersion: "20260520_older_migrations_failed"
  }
};

export default function TenantDetailConsole() {
  const params = useParams();
  const router = useRouter();
  const tenantId = (params?.tenantId as string) || "1";
  const [tenant, setTenant] = useState<TenantDetail | null>(MOCK_TENANTS[tenantId] || MOCK_TENANTS["1"]);
  const [actionLoading, setActionLoading] = useState(false);

  if (!tenant) {
    return <div className="text-center p-8 text-muted">Yükleniyor veya kiracı bulunamadı...</div>;
  }

  const handleStatusChange = async (newStatus: "active" | "suspended" | "deactivated") => {
    setActionLoading(true);
    // Simulate API calls: /suspend, /reactivate, /deactivate
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setTenant(prev => prev ? { ...prev, status: newStatus } : null);
    } catch (err) {
      alert("Durum güncellenirken hata oluştu.");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6 flex flex-col flex-1">
      {/* Console Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-card-border">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">{tenant.displayName}</h1>
            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
              tenant.status === "active" ? "bg-success/10 text-success" :
              tenant.status === "suspended" ? "bg-warning/10 text-warning" :
              tenant.status === "draft" ? "bg-primary/10 text-primary" :
              "bg-error/10 text-error"
            }`}>
              {tenant.status === "active" ? "Aktif" :
               tenant.status === "suspended" ? "Askıda" :
               tenant.status === "draft" ? "Taslak" : "Kapatıldı"}
            </span>
          </div>
          <p className="text-muted text-sm mt-1">
            Kiracı kimliği: <span className="font-mono text-xs text-foreground bg-card-border/30 px-1 py-0.5 rounded">{tenant.id}</span>
          </p>
        </div>

        <div className="flex gap-2">
          {tenant.status === "active" && (
            <button
              onClick={() => handleStatusChange("suspended")}
              disabled={actionLoading}
              className="inline-flex h-9 items-center justify-center rounded-lg border border-warning/40 bg-warning/5 text-warning px-4 text-xs font-semibold hover:bg-warning/10 disabled:opacity-50 transition-colors"
            >
              İşletmeyi Dondur (Suspend)
            </button>
          )}
          {tenant.status === "suspended" && (
            <button
              onClick={() => handleStatusChange("active")}
              disabled={actionLoading}
              className="inline-flex h-9 items-center justify-center rounded-lg border border-success/40 bg-success/5 text-success px-4 text-xs font-semibold hover:bg-success/10 disabled:opacity-50 transition-colors"
            >
              Tekrar Aktifleştir
            </button>
          )}
          {tenant.status !== "deactivated" && (
            <button
              onClick={() => {
                if (confirm("Bu kiracıyı tamamen kapatmak istediğinizden emin misiniz? Bu işlem geri alınamaz!")) {
                  handleStatusChange("deactivated");
                }
              }}
              disabled={actionLoading}
              className="inline-flex h-9 items-center justify-center rounded-lg border border-error/40 bg-error/5 text-error px-4 text-xs font-semibold hover:bg-error/10 disabled:opacity-50 transition-colors"
            >
              Kalıcı Kapat (Deactivate)
            </button>
          )}
        </div>
      </div>

      {/* Main Console Details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Col 1 & 2: Main Meta Info & Database Details */}
        <div className="md:col-span-2 space-y-6">
          {/* Metadata Card */}
          <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm space-y-4">
            <h2 className="text-lg font-bold border-b border-card-border pb-3">İşletme Detayları & Profil</h2>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted block text-xs uppercase font-semibold">Subdomain Slug</span>
                <span className="font-mono text-xs">{tenant.slug}</span>
              </div>
              <div>
                <span className="text-muted block text-xs uppercase font-semibold">Alan Adı (Domain)</span>
                <span className="font-mono text-xs text-primary">{tenant.domain}</span>
              </div>
              <div>
                <span className="text-muted block text-xs uppercase font-semibold">İşletme Sahibi</span>
                <span>{tenant.ownerName}</span>
              </div>
              <div>
                <span className="text-muted block text-xs uppercase font-semibold">Sahip E-posta</span>
                <span>{tenant.ownerEmail}</span>
              </div>
              <div>
                <span className="text-muted block text-xs uppercase font-semibold">Varsayılan Locale / Para Birimi</span>
                <span>{tenant.defaultLocale} / {tenant.defaultCurrency}</span>
              </div>
              <div>
                <span className="text-muted block text-xs uppercase font-semibold">Zaman Dilimi</span>
                <span>{tenant.timezone}</span>
              </div>
            </div>
          </div>

          {/* Database Configuration Card */}
          <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm space-y-4">
            <div className="flex justify-between items-center border-b border-card-border pb-3">
              <h2 className="text-lg font-bold">İzole Veritabanı (Database-Per-Tenant)</h2>
              <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-semibold ${
                tenant.databaseStatus === "healthy" ? "bg-success/10 text-success" : "bg-error/10 text-error"
              }`}>
                {tenant.databaseStatus === "healthy" ? "Sağlıklı" : "Hata Alındı"}
              </span>
            </div>

            <div className="space-y-4 text-sm">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <span className="text-muted block text-xs uppercase font-semibold">Veritabanı Adı (PostgreSQL)</span>
                  <span className="font-mono text-xs text-foreground bg-card-border/30 px-1 py-0.5 rounded">{tenant.databaseName}</span>
                </div>
                <div>
                  <span className="text-muted block text-xs uppercase font-semibold">Güncel Alembic Şema Sürümü</span>
                  <span className="font-mono text-xs">{tenant.schemaVersion}</span>
                </div>
              </div>

              {tenant.databaseStatus === "error" && (
                <div className="p-4 rounded-lg bg-error/10 border border-error/30 text-error text-xs space-y-2">
                  <p className="font-bold">Kurulum Hatası Tespit Edildi:</p>
                  <p>Masa tabloları schema migration Celery job sırasında lock timeout nedeniyle kilitlendi.</p>
                  <div className="pt-2">
                    <button className="bg-error text-white px-3 py-1 rounded text-xs font-bold hover:bg-error-hover transition-colors">
                      Kurulumu Yeniden Dene (Retry Provisioning)
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Col 3: Side Telemetry & Logs */}
        <div className="space-y-6">
          <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm space-y-4">
            <h2 className="text-lg font-bold border-b border-card-border pb-3">Canlı Telemetri</h2>
            
            <div className="space-y-4 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-muted">Masa Sayısı</span>
                <span className="font-bold">12</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted">İstasyon Sayısı</span>
                <span className="font-bold">3 (Mutfak, Bar, Fırın)</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted">Aktif Adisyon Sayısı</span>
                <span className="font-bold text-success">4 açık</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted">Son Sipariş</span>
                <span className="text-muted text-xs">2 dakika önce</span>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm space-y-4">
            <h2 className="text-lg font-bold border-b border-card-border pb-3">Platform Audit Logs</h2>
            <div className="space-y-3 text-[11px] leading-relaxed text-muted">
              <div>
                <p className="text-foreground font-semibold">12-May-2026 22:40</p>
                <p>Kiracı veritabanı schema-job (20260524) başarıyla tamamlandı.</p>
              </div>
              <div className="pt-2 border-t border-card-border">
                <p className="text-foreground font-semibold">10-May-2026 14:15</p>
                <p>Kiracı oluşturuldu (owner@customer-test.com, Plan: Pro)</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
