"use client";

import { useState } from "react";
import Link from "next/link";

export default function TenantStaffLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Simulate authentication lag
    setTimeout(() => {
      setLoading(false);
      if (email === "staff@bistro.com" && password === "bistro123") {
        window.location.href = "/console";
      } else {
        setError("E-posta adresi veya şifre hatalı. (İpucu: staff@bistro.com / bistro123)");
      }
    }, 1500);
  };

  return (
    <div className="flex flex-col flex-1 items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-card-bg border border-card-border p-8 rounded-2xl shadow-xl relative overflow-hidden">
        {/* Glowing header accent line */}
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-primary to-accent" />

        <div className="text-center">
          <span className="bg-primary/10 text-primary text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
            Personel Girişi
          </span>
          <h2 className="mt-6 text-3xl font-extrabold tracking-tight">İşletme Yönetimi</h2>
          <p className="mt-2 text-sm text-muted">
            Konsola bağlanmak için kimlik bilgilerinizi doğrulayın.
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          <div className="rounded-md shadow-sm space-y-4">
            <div>
              <label htmlFor="email-address" className="block text-xs font-semibold text-muted mb-1">
                E-posta Adresi
              </label>
              <input
                id="email-address"
                name="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="appearance-none rounded-xl relative block w-full px-4 py-3 border border-card-border bg-background placeholder-muted text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm transition-all"
                placeholder="staff@bistro.com"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-xs font-semibold text-muted mb-1">
                Şifre
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none rounded-xl relative block w-full px-4 py-3 border border-card-border bg-background placeholder-muted text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm transition-all"
                placeholder="••••••••"
              />
            </div>
          </div>

          {error && (
            <p className="text-xs text-error font-semibold text-center">{error}</p>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-bold rounded-xl text-background bg-primary hover:bg-primary-hover shadow-md shadow-primary/15 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Giriş Yapılıyor..." : "Giriş Yap"}
            </button>
          </div>
        </form>

        <div className="pt-6 border-t border-card-border text-center space-y-2">
          <p className="text-xs text-muted">
            Müşteri misiniz? 
          </p>
          <Link 
            href="/app" 
            className="inline-block text-xs font-bold text-accent hover:text-accent/80 transition-colors"
          >
            Müşteri Masa Siparişine Dön &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
