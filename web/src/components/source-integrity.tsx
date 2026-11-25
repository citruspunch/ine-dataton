import type { ReactNode } from "react";
import { ExternalLink, FileSpreadsheet, Fingerprint, Scale, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyButton } from "@/components/copy-button";
import { cn } from "@/lib/utils";
import {
  formatBytes,
  formatCompact,
  formatDate,
  formatSha,
  formatUtc,
  statusTone,
} from "@/lib/format";
import type { Manifest, SourceGroup } from "@/lib/types";

const groupBadge: Record<SourceGroup, string> = {
  DPIR: "bg-chart-2/10 text-chart-2 border-chart-2/20",
  IPMC: "bg-chart-1/10 text-chart-1 border-chart-1/20",
  ICC: "bg-chart-3/10 text-chart-3 border-chart-3/20",
  BASKETS: "bg-chart-4/10 text-chart-4 border-chart-4/20",
};

const statusBadge: Record<string, string> = {
  frozen: "border-amber-300/60 bg-amber-50 text-amber-800",
  current: "border-emerald-300/60 bg-emerald-50 text-emerald-800",
  limited: "border-sky-300/60 bg-sky-50 text-sky-800",
};

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[92px_1fr] gap-2 py-1.5 text-[10px] leading-relaxed">
      <span className="font-medium uppercase tracking-wide text-muted-foreground">{label}</span>
      <div className="min-w-0 text-foreground/80">{children}</div>
    </div>
  );
}

export function SourceIntegrity({
  manifest,
  activeSource,
}: {
  manifest: Manifest;
  activeSource: SourceGroup;
}) {
  const groupOrder = manifest.order;
  const datasets = [...manifest.datasets].sort((a, b) => {
    const activeA = a.group === activeSource ? 0 : 1;
    const activeB = b.group === activeSource ? 0 : 1;
    if (activeA !== activeB) return activeA - activeB;
    return groupOrder.indexOf(a.group) - groupOrder.indexOf(b.group);
  });

  return (
    <section id="trazabilidad" className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
      <div className="max-w-3xl">
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
          Trazabilidad
        </p>
        <h2 className="mt-2 font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
          Cada cifra tiene una URL, una hora UTC y un hash.
        </h2>
        <p className="mt-3 text-pretty text-sm leading-relaxed text-muted-foreground sm:text-base">
          El pipeline verifica primero la carpeta local. Si falta un archivo, lo descarga de una
          URL oficial del INE (datos.ine.gob.gt o www.ine.gob.gt), registra la marca de tiempo
          UTC y el SHA-256 de los bytes exactos, y lo cachea para que la aplicación funcione sin
          conexión.
        </p>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {datasets.map((dataset) => {
          const active = dataset.group === activeSource;
          return (
            <Card
              key={dataset.id}
              className={cn(
                "border-border/80 bg-card/85 transition-shadow",
                active && "ring-1 ring-primary/20",
              )}
            >
              <CardHeader className="gap-2 pb-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    <Badge variant="outline" className={cn("font-semibold", groupBadge[dataset.group])}>
                      {dataset.group}
                    </Badge>
                    {dataset.isDictionary ? (
                      <Badge variant="secondary" className="font-normal">
                        Diccionario
                      </Badge>
                    ) : null}
                  </div>
                  <Badge variant="outline" className={cn("font-medium", statusBadge[dataset.status])}>
                    {statusTone(dataset.status) === "warning"
                      ? "Congelado"
                      : dataset.status === "limited"
                        ? "Parcial"
                        : "Vigente"}
                  </Badge>
                </div>
                <CardTitle className="font-heading text-base leading-snug">{dataset.title}</CardTitle>
                <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                  <FileSpreadsheet className="size-3 shrink-0" aria-hidden />
                  <span className="truncate font-mono">{dataset.fileName}</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-1 pt-0">
                <Row label="Corte">
                  {dataset.isDictionary
                    ? "No aplica"
                    : `${formatDate(dataset.cutoff, dataset.group === "DPIR" ? "day" : "month")}`}
                </Row>
                <Row label="Registros">
                  {dataset.isDictionary
                    ? "Definiciones de variables"
                    : `${formatCompact(dataset.recordCount)} filas · ${formatCompact(dataset.canonicalCount)} canónicos`}
                </Row>
                <Row label="Descargado">
                  <span className="tabular">{formatUtc(dataset.downloadedAtUtc)}</span>
                  {dataset.retrieval === "local-cache" ? (
                    <span className="ml-1 text-muted-foreground">(cache local)</span>
                  ) : null}
                </Row>
                <Row label="SHA-256">
                  <div className="flex items-start gap-1">
                    <code className="break-all font-mono text-[9px] leading-relaxed text-foreground/70">
                      {formatSha(dataset.sha256, 28)}
                    </code>
                    {dataset.sha256 ? (
                      <CopyButton value={dataset.sha256} label="Hash" className="h-6 shrink-0 px-1.5" />
                    ) : null}
                  </div>
                </Row>
                <Row label="Tamaño">{formatBytes(dataset.bytes)}</Row>
                <Row label="Licencia">
                  <span className="inline-flex items-center gap-1">
                    <Scale className="size-3 shrink-0 text-muted-foreground" aria-hidden />
                    {dataset.license.url ? (
                      <a
                        href={dataset.license.url}
                        target="_blank"
                        rel="noreferrer"
                        className="underline decoration-border underline-offset-2 hover:text-foreground"
                      >
                        {dataset.license.title}
                      </a>
                    ) : (
                      dataset.license.title
                    )}
                  </span>
                </Row>
                <Row label="Fuente">
                  <a
                    href={dataset.sourcePage}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 break-all text-primary underline decoration-primary/30 underline-offset-2 hover:decoration-primary"
                  >
                    {new URL(dataset.sourcePage).host}
                    <ExternalLink className="size-2.5 shrink-0" aria-hidden />
                  </a>
                </Row>
                {dataset.url ? (
                  <Row label="Archivo">
                    <a
                      href={dataset.url}
                      target="_blank"
                      rel="noreferrer"
                      className="line-clamp-2 break-all text-[9px] text-muted-foreground underline decoration-border underline-offset-2 hover:text-foreground"
                    >
                      {dataset.url}
                    </a>
                  </Row>
                ) : null}
                <p className="mt-2 border-t border-border/60 pt-2 text-[9px] leading-relaxed text-muted-foreground">
                  {dataset.notes}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="mt-6 grid gap-3 lg:grid-cols-3">
        <div className="rounded-xl border border-border/80 bg-card/70 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold">
            <ShieldAlert className="size-4 text-primary" aria-hidden />
            Secreto estadístico
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">{manifest.privacy}</p>
        </div>
        <div className="rounded-xl border border-border/80 bg-card/70 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold">
            <Fingerprint className="size-4 text-primary" aria-hidden />
            Atribución
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
            {manifest.attribution}
          </p>
        </div>
        <div className="rounded-xl border border-border/80 bg-card/70 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold">
            <Scale className="size-4 text-primary" aria-hidden />
            Inteligencia artificial
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
            {manifest.aiDisclosure}
          </p>
        </div>
      </div>
    </section>
  );
}
