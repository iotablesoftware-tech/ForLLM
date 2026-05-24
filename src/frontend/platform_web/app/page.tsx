import Link from "next/link";

export default function Dashboard() {
  return (
    <div className="space-y-8 flex flex-col flex-1">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-card-border">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Platform Dashboard</h1>
          <p className="text-muted text-sm mt-1">
            İzole kiracı veritabanlarını, Celery arka plan kurulum süreçlerini ve telemetri loglarını tek ekrandan yönetin.
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/tenants/create"
            className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-background shadow-sm hover:bg-primary-hover transition-colors"
          >
            + Yeni Kiracı Ekle
          </Link>
        </div>
      </div>

      {/* Telemetry Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {/* Metric 1 */}
        <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm relative overflow-hidden group hover:border-primary/50 transition-colors">
          <div className="flex justify-between items-start">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted">Toplam Kiracı</p>
            <span className="text-xs font-medium text-success px-2 py-0.5 rounded bg-success/10">100% İzole</span>
          </div>
          <p className="text-3xl font-bold mt-2 tracking-tight">32</p>
          <div className="mt-4 flex items-center gap-1.5 text-xs text-muted">
            <span className="text-success font-semibold">12 aktif</span> son 7 gün
          </div>
        </div>

        {/* Metric 2 */}
        <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm relative overflow-hidden group hover:border-primary/50 transition-colors">
          <div className="flex justify-between items-start">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted">Aktif Celery İşleri</p>
            <span className="h-2 w-2 rounded-full bg-success animate-ping"></span>
          </div>
          <p className="text-3xl font-bold mt-2 tracking-tight">1</p>
          <div className="mt-4 flex items-center gap-1.5 text-xs text-muted">
            <span>Kuyrukta: 0, Çalışan: 1</span>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm relative overflow-hidden group hover:border-primary/50 transition-colors">
          <div className="flex justify-between items-start">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted">Global DB Durumu</p>
            <span className="text-xs font-medium text-success px-2 py-0.5 rounded bg-success/10">Sorunsuz</span>
          </div>
          <p className="text-3xl font-bold mt-2 tracking-tight">17.0</p>
          <div className="mt-4 flex items-center gap-1.5 text-xs text-muted">
            <span>PostgreSQL VPS Pool: Active</span>
          </div>
        </div>

        {/* Metric 4 */}
        <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm relative overflow-hidden group hover:border-primary/50 transition-colors">
          <div className="flex justify-between items-start">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted">Abonelik Gelirleri</p>
            <span className="text-xs font-medium text-primary px-2 py-0.5 rounded bg-primary/10">Monthly</span>
          </div>
          <p className="text-3xl font-bold mt-2 tracking-tight">₺184K</p>
          <div className="mt-4 flex items-center gap-1.5 text-xs text-muted">
            <span className="text-success font-semibold">+14.2%</span> geçen aya göre
          </div>
        </div>
      </div>

      {/* Main Dashboard Section */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Active Schema & Provisioning Tasks */}
        <div className="lg:col-span-2 rounded-xl border border-card-border bg-card-bg p-6 shadow-sm space-y-4">
          <div className="flex justify-between items-center pb-4 border-b border-card-border">
            <h2 className="text-lg font-bold">Son Kurulum İşleri (Celery Engine)</h2>
            <Link href="/jobs" className="text-xs font-semibold text-primary hover:underline">Tümünü Gör &rarr;</Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-muted border-b border-card-border">
                  <th className="pb-3 font-semibold">Kiracı Slug</th>
                  <th className="pb-3 font-semibold">İş Tipi</th>
                  <th className="pb-3 font-semibold">Başlangıç</th>
                  <th className="pb-3 font-semibold text-right">Durum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-card-border">
                <tr>
                  <td className="py-3.5 font-medium">bistro-ankara</td>
                  <td className="py-3.5 text-muted">Provisioning</td>
                  <td className="py-3.5 text-muted">10 dakika önce</td>
                  <td className="py-3.5 text-right">
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold bg-success/10 text-success">
                      Tamamlandı
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="py-3.5 font-medium">cafe-piazza</td>
                  <td className="py-3.5 text-muted">Schema Migrations</td>
                  <td className="py-3.5 text-muted">45 dakika önce</td>
                  <td className="py-3.5 text-right">
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold bg-success/10 text-success">
                      Tamamlandı
                    </span>
                  </td>
                </tr>
                <tr>
                  <td className="py-3.5 font-medium">burger-island</td>
                  <td className="py-3.5 text-muted">Provisioning</td>
                  <td className="py-3.5 text-muted">2 saat önce</td>
                  <td className="py-3.5 text-right">
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold bg-error/10 text-error">
                      Hata Aldı
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Caddy TLS & SSL Telemetry Status */}
        <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm space-y-4">
          <div className="pb-4 border-b border-card-border">
            <h2 className="text-lg font-bold">Caddy Gateway & SSL</h2>
          </div>
          
          <div className="space-y-4 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted">Caddy SSL Proxy</span>
              <span className="font-semibold text-success">Çalışıyor</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted">On-Demand TLS</span>
              <span className="font-semibold text-success">Aktif</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted">Aktif Sertifikalar</span>
              <span className="font-semibold">32 adet (Let's Encrypt)</span>
            </div>
            
            <div className="pt-4 border-t border-card-border space-y-2">
              <p className="text-xs text-muted leading-relaxed">
                Her kiracı subdomain'i (`*.iotables.net`) ilk DNS eşleşmesinde Caddy Gateway aracılığıyla `/validate-domain` kontrolü sonrasında otomatik HTTPS SSL sertifikası kazanır.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
