import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "INE Data Trust",
  description: "Validación técnica de agregados estadísticos publicados",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <header className="border-b-4 border-brand-dark bg-brand text-white print:hidden">
          <div className="mx-auto flex min-h-16 max-w-6xl items-center justify-between gap-6 px-6">
            <Link href="/" className="flex items-baseline gap-3">
              <span className="text-lg font-semibold tracking-tight">
                INE Data Trust
              </span>
            </Link>
            <nav className="flex items-center gap-1 text-sm">
              <Link
                href="/review"
                className="rounded px-3 py-1.5 text-brand-soft transition hover:bg-white/10 hover:text-white"
              >
                Revisión técnica
              </Link>
              <Link
                href="/"
                className="rounded px-3 py-1.5 text-brand-soft transition hover:bg-white/10 hover:text-white"
              >
                Consulta
              </Link>
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>

        <footer className="mx-auto max-w-6xl px-6 pb-12 text-xs text-muted print:hidden">
          <p>
            Validación técnica. No certifica, no corrige, no publica en CKAN y no
            constituye aprobación del INE. Los datos conservan su licencia original.
          </p>
        </footer>
      </body>
    </html>
  );
}
