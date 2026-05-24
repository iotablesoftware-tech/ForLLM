"use client";

import TableStatusGrid from "./_components/TableStatusGrid";
import ActiveOrders from "./_components/ActiveOrders";

export default function RestaurantConsole() {
  return (
    <div className="space-y-8 flex flex-col flex-1">
      {/* Welcome & System Telemetry Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-card-border">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Restoran Personel Konsolu</h1>
          <p className="text-muted text-sm mt-1">
            Masa doluluk oranlarını, anlık garson çağrılarını ve mutfak sipariş akışını bu panelden gerçek zamanlı yönetin.
          </p>
        </div>
        
        <div className="flex gap-3">
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-card-bg border border-card-border text-xs font-semibold">
            <span className="h-2 w-2 rounded-full bg-accent animate-pulse"></span>
            Yazıcı Sunucusu: <span className="text-accent font-bold">Aktif</span>
          </div>
        </div>
      </div>

      {/* Main Grid split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <TableStatusGrid />
        </div>
        
        <div className="lg:col-span-1">
          <ActiveOrders />
        </div>
      </div>
    </div>
  );
}
