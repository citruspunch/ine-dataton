import Link from "next/link";
import { Database, ExternalLink, Landmark } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/format";
import type { Summary } from "@/lib/types";

export function SiteHeader({ summary }: { summary: Summary }) {
  const cutoffs = Object.values(summary.groups)
    .map((group) => group.cutoff)
    .filter((value): value is string => Boolean(value))
    .sort();
  const latest = cutoffs[cutoffs.length - 1];

  return (
    <header className="sticky top-0 z-50 border-b border-border/70 bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <Link href="#inicio" className="group flex items-center gap-2.5">
          <span className="grid size-9 place-items-center rounded-lg bg-primary text-primary-foreground shadow-sm">
            <Landmark className="size-4.5" aria-hidden />
          </span>
          <span className="leading-tight">
            <span className="block font-heading text-[17px] font-semibold tracking-tight">
              Mesa de Precios
            </span>
            <span className="block text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
              INE · Datatón 2026
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-6 text-sm text-muted-foreground md:flex">
          <a className="transition-colors hover:text-foreground" href="#consulta">
            Consulta
          </a>
          <a className="transition-colors hover:text-foreground" href="#trazabilidad">
            Trazabilidad
          </a>
          <a className="transition-colors hover:text-foreground" href="#metodologia">
            Metodología
          </a>
        </nav>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="hidden gap-1.5 border-success/30 bg-success/5 text-success sm:flex">
            <span className="size-1.5 rounded-full bg-success" />
            Datos oficiales
          </Badge>
          {latest ? (
            <Badge variant="outline" className="hidden font-normal text-muted-foreground lg:flex">
              <Database className="size-3" aria-hidden />
              Corte {formatDate(latest, "month")}
            </Badge>
          ) : null}
          <a
            href="https://datos.ine.gob.gt"
            target="_blank"
            rel="noreferrer"
            aria-label="Abrir el portal de datos abiertos del INE"
            className="grid size-8 place-items-center rounded-lg border border-border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <ExternalLink className="size-3.5" aria-hidden />
          </a>
        </div>
      </div>
    </header>
  );
}
