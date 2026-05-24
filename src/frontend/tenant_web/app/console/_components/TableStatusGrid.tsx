"use client";

import { useState, useEffect } from "react";
import { listTablesAction, TableStatus } from "../_api/billingActions";

export default function TableStatusGrid() {
  const [tables, setTables] = useState<TableStatus[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch tables from backend on mount
  useEffect(() => {
    async function loadTables() {
      try {
        setLoading(true);
        const data = await listTablesAction();
        setTables(data);
        setLoading(false);
      } catch (err: any) {
        setError(err.message || "Masalar yüklenemedi.");
        setLoading(false);
      }
    }
    loadTables();
  }, []);

  // Poll tables status every 5 seconds
  useEffect(() => {
    if (loading || error) return;

    const interval = setInterval(async () => {
      try {
        const data = await listTablesAction();
        setTables(data);
      } catch (err) {
        // Silent catch for background polling
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [loading, error]);

  const handleClearAlert = (id: string) => {
    setTables(current =>
      current.map(t =>
        t.id === id && (t.status === "Garson Çağırıyor" || t.status === "Hesap İstiyor")
          ? { ...t, status: "Dolu" }
          : t
      )
    );
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-card-border bg-card-bg p-6 shadow-sm flex flex-col items-center justify-center h-48 space-y-3">
        <span className="h-6 w-6 rounded-full border-2 border-primary border-t-transparent animate-spin" />
        <p className="text-muted text-xs font-semibold">Masalar yükleniyor...</p>
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
        <h2 className="text-lg font-bold">Masa Yerleşim & Çağrı Planı</h2>
        <div className="flex items-center gap-4 text-xs font-semibold">
          <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded bg-muted/30" /> Boş</span>
          <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded bg-accent/25" /> Dolu</span>
          <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded bg-error/30" /> Çağrı</span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {tables.map(table => {
          const isCalling = table.status === "Garson Çağırıyor" || table.status === "Hesap İstiyor";
          const isDolu = table.status === "Dolu";
          return (
            <div
              key={table.id}
              className={`rounded-xl border p-4 relative flex flex-col justify-between h-32 transition-all ${
                table.status === "Boş"
                  ? "border-card-border bg-background/40 hover:border-accent/40"
                  : isCalling
                  ? "border-error bg-error/10 animate-pulse"
                  : "border-accent/40 bg-accent/5 hover:border-accent/80"
              }`}
            >
              <div>
                <div className="flex justify-between items-start">
                  <h3 className="font-extrabold text-sm text-foreground">{table.name}</h3>
                  <span className="text-[10px] text-muted font-bold">Cap: {table.capacity}</span>
                </div>
                
                {isCalling && (
                  <p className="text-[10px] font-extrabold text-error mt-2.5 flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-error animate-ping" />
                    {table.status}
                  </p>
                )}

                {isDolu && (
                  <div className="mt-2 space-y-1">
                    <p className="text-[10px] font-semibold text-muted">
                      Hesap: <strong className="text-accent">₺{table.bill}</strong>
                    </p>
                    {table.bill_session_id && (
                      <span className="text-[9px] text-primary/70 block font-semibold">
                        Adisyon: {table.bill_session_id.slice(0, 8)}
                      </span>
                    )}
                  </div>
                )}

                {table.status === "Boş" && (
                  <p className="text-[10px] text-muted mt-2">Kullanıma hazır</p>
                )}
              </div>

              {isCalling && (
                <button
                  onClick={() => handleClearAlert(table.id)}
                  className="w-full mt-2 py-1 rounded bg-error/25 hover:bg-error text-error hover:text-background text-[10px] font-bold transition-all text-center"
                >
                  Çağrıyı Kapat
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
