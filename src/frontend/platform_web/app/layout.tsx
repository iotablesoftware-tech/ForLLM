import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "IoTable platform_web | Platform Owner Console",
  description: "Central platform operations, tenant registry provisioning, dynamic migrations, and trust logs.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr" className="h-full">
      <body className="min-h-screen bg-background text-foreground font-sans flex flex-col antialiased">
        {/* Central Platform Navigation Bar */}
        <header className="sticky top-0 z-50 w-full border-b border-card-border bg-background/80 backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-8">
              <Link href="/" className="flex items-center gap-2 font-bold text-xl tracking-tight text-primary">
                <span className="bg-primary text-background px-2 py-0.5 rounded-md font-extrabold text-sm">IoT</span>
                IoTable <span className="text-xs font-semibold text-muted px-1.5 py-0.5 rounded border border-card-border">platform</span>
              </Link>
              
              <nav className="hidden md:flex items-center gap-6">
                <Link href="/" className="text-sm font-medium transition-colors hover:text-primary">
                  Dashboard
                </Link>
                <Link href="/tenants" className="text-sm font-medium transition-colors hover:text-primary">
                  Kiracı Rehberi
                </Link>
                <Link href="/tenants/create" className="text-sm font-medium transition-colors hover:text-primary">
                  Kurulum Sihirbazı
                </Link>
              </nav>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-card-border bg-card-bg text-xs font-medium">
                <span className="h-2 w-2 rounded-full bg-success animate-pulse"></span>
                Platform Active
              </div>
              <div className="h-8 w-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center text-xs font-extrabold text-primary">
                PO
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col">
          {children}
        </main>

        {/* Global Footer */}
        <footer className="border-t border-card-border bg-card-bg py-6 text-center text-xs text-muted">
          &copy; 2026 IoTable Platform Control Plane. All rights reserved. Only platform_owners authorized.
        </footer>
      </body>
    </html>
  );
}
