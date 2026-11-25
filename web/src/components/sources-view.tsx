import type { ReactNode } from "react";
import { ChevronDown, ExternalLink, FileSpreadsheet, Scale } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { CopyButton } from "@/components/copy-button";
import { cn } from "@/lib/utils";
import {
  formatBytes,
  formatCompact,
  formatDate,
  formatSha,
  formatUtc,
} from "@/lib/format";
import type { DatasetManifest, Manifest } from "@/lib/types";

const statusStyles: Record<string, string> = {
  frozen: "border-amber-300 bg-amber-50 text-amber-800",
  current: "border-emerald-300 bg-emerald-50 text-emerald-800",
  limited: "border-sky-300 bg-sky-50 text-sky-800",
};

function licenseShort(dataset: DatasetManifest): string {
  if (dataset.license.id === "odc-by") return "ODC-BY";
  if (dataset.license.id === "cc-by") return "CC-BY";
  return "No declarada";
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[92px_1fr] gap-3 text-sm">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <div className="min-w-0">{children}</div>
    </div>
  );
}

export function SourcesView({ manifest }: { manifest: Manifest }) {
  return (
    <section className="pb-12">
      <div className="mb-6 max-w-2xl">
        <h2 className="font-heading text-2xl font-semibold tracking-tight">Cortes y licencias</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          Cada archivo tiene una URL oficial, una hora UTC de descarga y un SHA-256. El corte
          se lee del último dato válido dentro del archivo, no del nombre.
        </p>
      </div>

      <div className="hidden grid-cols-[1.6fr_0.8fr_0.7fr_24px] gap-4 border-b border-border/70 pb-2 text-xs font-medium text-muted-foreground sm:grid">
        <span>Archivo</span>
        <span>Corte</span>
        <span>Licencia</span>
        <span />
      </div>

      <div>
        {manifest.datasets.map((dataset) => (
          <details key={dataset.id} className="group border-b border-border/60">
            <summary className="flex cursor-pointer list-none flex-col gap-2 py-4 sm:grid sm:grid-cols-[1.6fr_0.8fr_0.7fr_24px] sm:items-center sm:gap-4">
              <div className="flex min-w-0 items-start gap-3">
                <Badge variant="outline" className="mt-0.5 shrink-0 font-medium">
                  {dataset.group}
                </Badge>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium">{dataset.title}</span>
                    <Badge
                      variant="outline"
                      className={cn("h-5 px-1.5 text-[11px] font-medium", statusStyles[dataset.status])}
                    >
                      {dataset.status === "frozen" ? "Congelado" : dataset.status === "limited" ? "Parcial" : "Vigente"}
                    </Badge>
                  </div>
                  <div className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                    <FileSpreadsheet className="size-3 shrink-0" aria-hidden />
                    <span className="truncate font-mono">{dataset.fileName}</span>
                  </div>
                </div>
              </div>
              <div className="text-sm">
                {dataset.isDictionary ? "—" : formatDate(dataset.cutoff, dataset.group === "DPIR" ? "day" : "month")}
              </div>
              <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <Scale className="size-3.5 shrink-0" aria-hidden />
                {licenseShort(dataset)}
              </div>
              <ChevronDown
                className="size-4 text-muted-foreground transition-transform group-open:rotate-180"
                aria-hidden
              />
            </summary>

            <div className="grid gap-4 pb-6 sm:grid-cols-2">
              <div className="space-y-2.5">
                <Row label="Descargado">
                  <span className="tabular">{formatUtc(dataset.downloadedAtUtc)}</span>
                </Row>
                <Row label="SHA-256">
                  <div className="flex flex-wrap items-center gap-2">
                    <code className="font-mono text-xs text-muted-foreground">
                      {formatSha(dataset.sha256, 24)}
                    </code>
                    {dataset.sha256 ? <CopyButton value={dataset.sha256} label="Copiar" /> : null}
                  </div>
                </Row>
                <Row label="Tamaño">
                  <span>{formatBytes(dataset.bytes)}</span>
                </Row>
                <Row label="Registros">
                  <span>
                    {dataset.isDictionary
                      ? "Definiciones de variables"
                      : `${formatCompact(dataset.recordCount)} filas · ${formatCompact(dataset.canonicalCount)} canónicos`}
                  </span>
                </Row>
              </div>
              <div className="space-y-2.5">
                <Row label="Archivo">
                  {dataset.url ? (
                    <a
                      href={dataset.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-start gap-1 break-all text-primary underline-offset-4 hover:underline"
                    >
                      <span className="line-clamp-2">{dataset.url}</span>
                      <ExternalLink className="mt-0.5 size-3 shrink-0" aria-hidden />
                    </a>
                  ) : (
                    <span className="text-muted-foreground">No registrado</span>
                  )}
                </Row>
                <Row label="Origen">
                  <a
                    href={dataset.sourcePage}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-primary underline-offset-4 hover:underline"
                  >
                    Página del INE
                    <ExternalLink className="size-3" aria-hidden />
                  </a>
                </Row>
                <Row label="Licencia">
                  <span>{dataset.license.title}</span>
                </Row>
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground sm:col-span-2">
                {dataset.coverage}
              </p>
              <p className="text-xs leading-relaxed text-muted-foreground sm:col-span-2">
                {dataset.notes}
              </p>
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
