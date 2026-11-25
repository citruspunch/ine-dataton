import Link from "next/link";
import { BookOpen, ExternalLink, Landmark } from "lucide-react";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/70 bg-background/90 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-3 px-4 sm:h-16 sm:px-6 lg:px-8">
        <Link href="/" className="flex min-w-0 items-center gap-2.5">
          <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-primary text-primary-foreground sm:size-9">
            <Landmark className="size-4" aria-hidden />
          </span>
          <span className="min-w-0 leading-tight">
            <span className="block whitespace-nowrap font-heading text-base font-semibold tracking-tight sm:text-[17px]">
              Mesa de Precios
            </span>
            <span className="hidden text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground sm:block">
              INE · Datatón 2026
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-5 text-sm text-muted-foreground md:flex">
          <a className="transition-colors hover:text-foreground" href="/#consulta">
            Consulta
          </a>
          <Link className="transition-colors hover:text-foreground" href="/fuentes">
            Fuentes y método
          </Link>
        </nav>

        <div className="flex items-center gap-1.5">
          <Link
            href="/fuentes"
            aria-label="Fuentes y método"
            className="grid size-9 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground md:hidden"
          >
            <BookOpen className="size-4" aria-hidden />
          </Link>
          <a
            href="https://datos.ine.gob.gt"
            target="_blank"
            rel="noreferrer"
            aria-label="Abrir el portal de datos abiertos del INE"
            className="hidden size-8 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground sm:grid"
          >
            <ExternalLink className="size-4" aria-hidden />
          </a>
        </div>
      </div>
    </header>
  );
}
