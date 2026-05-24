"use client";

import { useState, useEffect } from "react";
import { listActiveOrdersAction, updateOrderStatusAction, KitchenOrder } from "../_api/billingActions";

export default function ActiveOrders() {
  const [orders, setOrders] = useState<KitchenOrder[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch active orders from backend on mount
  useEffect(() => {
    async function loadOrders() {
      try {
        setLoading(true);
        const data = await listActiveOrdersAction();
        setOrders(data);
        setLoading(false);
      } catch (err: any) {
        setError(err.message || "Siparişler yüklenemedi.");
        setLoading(false);
      }
    }
    loadOrders();
  }, []);

  // Poll active orders every 5 seconds
  useEffect(() => {
    if (loading || error) return;

    const interval = setInterval(async () => {
      try {
        const data = await listActiveOrdersAction();
        setOrders(data);
      } catch (err) {
        // Silent catch for background polling
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [loading, error]);

  const handleUpdateStatus = async (id: string, newStatus: string) => {
    try {
      const statusMap: Record<string, string> = {
        "Hazırlanıyor": "preparing",
        "served": "served",
      };
      const backendStatus = statusMap[newStatus] || newStatus;
      
      await updateOrderStatusAction(id, backendStatus);
      
      const data = await listActiveOrdersAction();
      setOrders(data);
    } catch (err: any) {
      console.error("Order status update failed:", err);
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm flex flex-col items-center justify-center h-48 space-y-3">
        <span className="h-6 w-6 rounded-full border-2 border-primary border-t-transparent animate-spin" />
        <p className="text-muted text-xs font-semibold">Sipariş akışı yükleniyor...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm flex flex-col items-center justify-center h-48 text-center space-y-3 text-error text-xs font-semibold">
        <p>{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-3 py-1.5 bg-primary text-background rounded-lg font-bold"
        >
          Yeniden Yükle
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm space-y-6">
      <div className="flex justify-between items-center pb-4 border-b border-card-border">
        <h2 className="text-lg font-bold">Aktif Mutfak Siparişleri</h2>
        <span className="text-xs px-2.5 py-1 rounded bg-orange-500/10 text-primary font-bold animate-pulse">
          Canlı İzleme
        </span>
      </div>

      <div className="space-y-4">
        {orders.length === 0 ? (
          <div className="py-8 text-center text-muted text-sm space-y-1">
            <p>Aktif sipariş bulunmuyor.</p>
            <p className="text-[10px]">Müşteriler sipariş verdiğinde burada listelenecektir.</p>
          </div>
        ) : (
          orders.map(order => (
            <div
              key={order.id}
              className={`border rounded-xl p-4 transition-colors ${
                order.status === "Sırada"
                  ? "border-primary/30 bg-primary/5"
                  : order.status === "Hazırlanıyor"
                  ? "border-warning/30 bg-warning/5"
                  : "border-card-border bg-card-bg/30"
              }`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-xs font-bold text-muted">{order.id.slice(0, 8).toUpperCase()}</span>
                  <h3 className="font-extrabold text-base text-foreground mt-0.5">{order.table}</h3>
                </div>
                <span
                  className={`text-xs px-2.5 py-1 rounded-full font-bold ${
                    order.status === "Sırada"
                      ? "bg-primary text-background"
                      : order.status === "Hazırlanıyor"
                      ? "bg-warning text-stone-900"
                      : "bg-accent/20 text-accent"
                  }`}
                >
                  {order.status}
                </span>
              </div>

              {/* Order Items */}
              <div className="mt-3 space-y-1">
                {order.items.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm text-foreground/90 font-medium">
                    <span>{item.name}</span>
                    <span className="text-muted">x{item.quantity}</span>
                  </div>
                ))}
              </div>

              <div className="mt-4 pt-3 border-t border-card-border/50 flex justify-between items-center text-xs">
                <span className="text-muted">Tutar: <strong className="text-foreground">₺{order.total}</strong> | {order.time}</span>
                
                <div className="flex gap-2">
                  {order.status === "Sırada" && (
                    <button
                      onClick={() => handleUpdateStatus(order.id, "Hazırlanıyor")}
                      className="px-2.5 py-1.5 rounded-lg bg-warning hover:bg-amber-500 text-stone-950 font-bold transition-all"
                    >
                      Hazırla
                    </button>
                  )}
                  {order.status === "Hazırlanıyor" && (
                    <button
                      onClick={() => handleUpdateStatus(order.id, "served")}
                      className="px-2.5 py-1.5 rounded-lg bg-accent hover:bg-emerald-600 text-background font-bold transition-all"
                    >
                      Teslim Et
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
