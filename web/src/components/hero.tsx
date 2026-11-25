import { ArrowRight, CheckCircle2, FileSearch, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate, formatCompact } from "@/lib/format";
import type { SourceGroup, Summary } from "@/lib/types";

const dotTone: Record<SourceGroup, string> = {
  DPIR: "bg-chart-2",
  IPMC: "bg-chart-1",
  ICC: "bg-chart-3",
  BASKETS: "bg-chart-4",
};

const statusTone: Record<string, string> = {
  frozen: "text-amber-700",
  current: "text-emerald-700",
  limited: "text-sky-700",
};

export function Hero({ summary, activeSource }: { summary: Summary; activeSource: SourceGroup }) {
  const groups = summary.order.map((group) => summary.groups[group]);
  const latest = groups
    .map((group) => group.cutoff)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1);

  return (
    <section id="inicio" className="relative overflow-hidden border-b border-border/60">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 pb-10 pt-12 sm:px-6 lg:grid-cols-[1.25fr_0.75fr] lg:gap-14 lg:px-8 lg:pb-14 lg:pt-16">
        <div className="max-w-3xl">
          <div className="mb-5 flex flex-wrap items-center gap-2">
            <Badge className="bg-primary/10 text-primary hover:bg-primary/10">
              Categoría tecnológica
            </Badge>
            <Badge variant="outline" className="font-normal text-muted-foreground">
              Compras municipales · Guatemala
            </Badge>
          </div>

          <h1 className="font-heading text-4xl font-semibold leading-[1.05] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            Antes de cotizar,
            <span className="block text-primary">mire la evidencia.</span>
          </h1>

          <p className="mt-5 max-w-2xl text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg">
            Una mesa de consulta y auditoría para compradores municipales: precios de
            referencia observados, índices de construcción y costos de canasta del INE.
            Cada cifra muestra su <strong className="font-medium text-foreground">corte real</strong>,
            su cobertura y sus alertas de calidad antes de que un dato entre en una
            cotización.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1.5">
              <CheckCircle2 className="size-4 text-success" aria-hidden />
              Sin identificación de proveedores
            </span>
            <span className="inline-flex items-center gap-1.5">
              <ShieldCheck className="size-4 text-success" aria-hidden />
              Procedencia verificable
            </span>
            <span className="inline-flex items-center gap-1.5">
              <FileSearch className="size-4 text-success" aria-hidden />
              {formatCompact(summary.totalRecords)} observaciones
            </span>
          </div>

          <a
            href="#consulta"
            className="mt-8 inline-flex items-center gap-2 text-sm font-medium text-primary underline-offset-4 hover:underline"
          >
            Ir a la consulta
            <ArrowRight className="size-4" aria-hidden />
          </a>
        </div>

        <Card className="self-start border-border/80 bg-card/85 shadow-sm backdrop-blur">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                  Registro de cortes
                </p>
                <CardTitle className="mt-1 font-heading text-xl">Qué fecha tienen los datos</CardTitle>
              </div>
              <Badge variant="outline" className="shrink-0 font-normal">
                {latest ? formatDate(latest, "month") : "Sin datos"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="divide-y divide-border/70">
              {groups.map((group) => (
                <div key={group.id} className="flex items-center justify-between gap-4 py-3">
                  <div className="flex min-w-0 items-center gap-2.5">
                    <span className={`size-2 shrink-0 rounded-full ${dotTone[group.id]}`} />
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-medium">{group.shortLabel}</span>
                        {group.id === activeSource ? (
                          <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-primary">
                            activa
                          </span>
                        ) : null}
                      </div>
                      <p className="truncate text-[11px] text-muted-foreground">{group.tagline}</p>
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    <div className="text-sm font-medium tabular">
                      {formatDate(group.cutoff, group.granularity)}
                    </div>
                    <div className={`text-[10px] font-medium uppercase tracking-wide ${statusTone[group.status] ?? "text-muted-foreground"}`}>
                      {group.statusLabel}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-4 border-t border-border/70 pt-3 text-[11px] leading-relaxed text-muted-foreground">
              El corte se lee de la última fecha con dato válido dentro de cada archivo,
              no del nombre del archivo ni de la fecha de publicación.
            </p>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
