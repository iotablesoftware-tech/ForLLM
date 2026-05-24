"use client";

import { useState } from "react";
import useRouter from "next/navigation";
import Link from "next/link";

export default function AppHome() {
  const [tableNumber, setTableNumber] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!tableNumber.trim() || isNaN(Number(tableNumber))) {
      setError("Lütfen geçerli bir masa numarası giriniz.");
      return;
    }
    
    // Simulate table token generation
    window.location.href = `/g/table-token-${tableNumber}`;
  };

  return (
    <div className="flex flex-col flex-1 items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-card-bg border border-card-border p-8 rounded-2xl shadow-xl relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-primary via-orange-500 to-accent" />

        <div className="text-center">
          <span className="bg-primary/10 text-primary text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
            IoTable Dijital Menü
          </span>
          <h2 className="mt-6 text-3xl font-extrabold tracking-tight">Masanıza Bağlanın</h2>
          <p className="mt-2 text-sm text-muted">
            Lütfen masanızda bulunan QR kodu okutun veya aşağıya masa numaranızı yazarak sipariş vermeye başlayın.
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="table-number" className="sr-only">
                Masa Numarası
              </label>
              <input
                id="table-number"
                name="table"
                type="text"
                required
                value={tableNumber}
                onChange={(e) => {
                  setTableNumber(e.target.value);
                  if (error) setError(null);
                }}
                className="appearance-none rounded-xl relative block w-full px-4 py-3 border border-card-border bg-background placeholder-muted text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-center font-bold text-lg tracking-wide transition-all"
                placeholder="Masa Numarası (Örn: 12)"
              />
            </div>
          </div>

          {error && (
            <p className="text-xs text-error font-medium text-center">{error}</p>
          )}

          <div>
            <button
              type="submit"
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-bold rounded-xl text-background bg-primary hover:bg-primary-hover shadow-md shadow-primary/15 transition-all"
            >
              Masa Menüsünü Aç &rarr;
            </button>
          </div>
        </form>

        <div className="pt-6 border-t border-card-border text-center space-y-2">
          <p className="text-xs text-muted">
            Personel misiniz? 
          </p>
          <Link 
            href="/login" 
            className="inline-block text-xs font-bold text-accent hover:text-accent/80 transition-colors"
          >
            Yönetim Konsoluna Git &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
