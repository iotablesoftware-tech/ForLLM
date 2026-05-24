import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "IoTable Restaurant | Masa Sipariş & Yönetim",
  description: "Gerçek zamanlı kolaboratif sepet, dijital menü ve restoran yönetim konsolu.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr" className="h-full">
      <body className="min-h-screen bg-background text-foreground font-sans flex flex-col antialiased">
        {/* Modern Navbar with dynamic background */}
        <header className="sticky top-0 z-50 w-full border-b border-card-border bg-background/85 backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-8">
              <Link href="/app" className="flex items-center gap-2 font-bold text-xl tracking-tight text-primary">
                <span className="bg-primary text-background px-2.5 py-0.5 rounded-lg font-extrabold text-sm">IoT</span>
                IoTable <span className="text-xs font-semibold text-accent px-1.5 py-0.5 rounded border border-card-border bg-accent/5">restaurant</span>
              </Link>
              
              <nav className="hidden md:flex items-center gap-6">
                <Link href="/g/test-table-123" className="text-sm font-medium transition-colors hover:text-primary">
                  Dijital Menü & Sipariş (Masa 12)
                </Link>
                <Link href="/console" className="text-sm font-medium transition-colors hover:text-primary">
                  Personel Konsolu
                </Link>
              </nav>
            </div>
            
            <div className="flex items-center gap-4">
              <Link 
                href="/login"
                className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-card-border hover:bg-card-bg transition-colors"
              >
                Personel Girişi
              </Link>
              <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-accent/10 border border-accent/20 text-xs font-semibold text-accent">
                <span className="h-1.5 w-1.5 rounded-full bg-accent animate-ping"></span>
                Canlı Bağlantı
              </div>
            </div>
          </div>
        </header>

        {/* Dynamic App Content */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col">
          {children}
        </main>

        {/* Elegant Footer */}
        <footer className="border-t border-card-border bg-card-bg/50 py-6 text-center text-xs text-muted">
          &copy; 2026 IoTable Tenant Network. Güçlü, 100% izole restoran işletim altyapısı.
        </footer>
      </body>
    </html>
  );
}
