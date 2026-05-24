"use client";

import { useState } from "react";
import Link from "next/link";

interface TenantSummary {
  id: string;
  displayName: string;
  slug: string;
  domain: string;
  status: "active" | "draft" | "suspended" | "deactivated";
  businessType: string;
  createdAt: string;
}

const INITIAL_TENANTS: TenantSummary[] = [
  {
    id: "1",
    displayName: "Ankara Gurme Bistro",
    slug: "bistro-ankara",
    domain: "bistro-ankara.iotables.net",
    status: "active",
    businessType: "restaurant",
    createdAt: "2026-05-20"
  },
  {
    id: "2",
    displayName: "Piazza Coffee & Bakery",
    slug: "cafe-piazza",
    domain: "cafe-piazza.iotables.net",
    status: "active",
    businessType: "cafe",
    createdAt: "2026-05-22"
  },
  {
    id: "3",
    displayName: "Burger Island Express",
    slug: "burger-island",
    domain: "burger-island.iotables.net",
    status: "suspended",
    businessType: "fast_food",
    createdAt: "2026-05-18"
  },
  {
    id: "4",
    displayName: "Ege Ev Yemekleri",
    slug: "ege-mutfagi",
    domain: "ege-mutfagi.iotables.net",
    status: "draft",
    businessType: "restaurant",
    createdAt: "2026-05-24"
  }
];

export default function TenantDirectory() {
  const [tenants] = useState<TenantSummary[]>(INITIAL_TENANTS);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filteredTenants = tenants.filter(t => {
    const matchesSearch = t.displayName.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          t.slug.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || t.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 flex flex-col flex-1">
      {/* Directory Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-card-border">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Kiracı Rehberi</h1>
          <p className="text-muted text-sm mt-1">Platforma kayıtlı cafe ve restoran işletmelerini listeleyin, durumlarını kontrol edin.</p>
        </div>
        <Link
          href="/tenants/create"
          className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-background hover:bg-primary-hover transition-colors"
        >
          + Yeni Kiracı
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <input
            type="text"
            placeholder="İşletme adı veya slug ile ara..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-10 rounded-lg border border-card-border bg-card-bg px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <div className="w-full sm:w-48">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full h-10 rounded-lg border border-card-border bg-card-bg px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="all">Tüm Durumlar</option>
            <option value="active">Aktif</option>
            <option value="draft">Taslak</option>
            <option value="suspended">Askıya Alınmış</option>
            <option value="deactivated">Kapatılmış</option>
          </select>
        </div>
      </div>

      {/* Directory Table Card */}
      <div className="rounded-xl border border-card-border bg-card-bg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-muted border-b border-card-border bg-background/30">
                <th className="p-4 font-semibold">Kiracı Adı / Slug</th>
                <th className="p-4 font-semibold">Domain</th>
                <th className="p-4 font-semibold">Tür</th>
                <th className="p-4 font-semibold">Kayıt Tarihi</th>
                <th className="p-4 font-semibold">Durum</th>
                <th className="p-4 font-semibold text-right">İşlem</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-card-border">
              {filteredTenants.length > 0 ? (
                filteredTenants.map((tenant) => (
                  <tr key={tenant.id} className="hover:bg-background/20 transition-colors">
                    <td className="p-4">
                      <div className="font-semibold text-foreground">{tenant.displayName}</div>
                      <div className="text-xs text-muted font-mono">{tenant.slug}</div>
                    </td>
                    <td className="p-4 text-muted font-mono text-xs">{tenant.domain}</td>
                    <td className="p-4 capitalize text-xs">{tenant.businessType.replace("_", " ")}</td>
                    <td className="p-4 text-muted text-xs">{tenant.createdAt}</td>
                    <td className="p-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        tenant.status === "active" ? "bg-success/10 text-success" :
                        tenant.status === "suspended" ? "bg-warning/10 text-warning" :
                        tenant.status === "draft" ? "bg-primary/10 text-primary" :
                        "bg-error/10 text-error"
                      }`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${
                          tenant.status === "active" ? "bg-success" :
                          tenant.status === "suspended" ? "bg-warning" :
                          tenant.status === "draft" ? "bg-primary" :
                          "bg-error"
                        }`}></span>
                        {tenant.status === "active" ? "Aktif" :
                         tenant.status === "suspended" ? "Askıda" :
                         tenant.status === "draft" ? "Taslak" : "Kapatıldı"}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <Link
                        href={`/tenants/${tenant.id}`}
                        className="inline-flex items-center justify-center h-8 rounded border border-card-border px-3 text-xs font-semibold text-muted hover:text-primary hover:border-primary/50 transition-colors"
                      >
                        Yönet
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-muted">
                    Eşleşen kiracı kaydı bulunamadı.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
