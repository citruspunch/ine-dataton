"use client";

import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Database,
  FileSpreadsheet,
  Hash,
  Info,
  Scale,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { basketData } from "@/lib/data";
import {
  formatFileSize,
  formatNumber,
  formatSignedPercent,
  formatUtcStamp,
} from "@/lib/format";
import type { SourceEntry } from "@/lib/types";

function LicenseBadge({ source }: { source: SourceEntry }) {
  if (source.license.status === "declarada") {
    return (
      <Badge
        variant="outline"
        className="gap-1 border-emerald-200 bg-emerald-50 text-[10.5px] font-medium text-emerald-800"
      >
        <CheckCircle2 className="size-3" />
        CC BY 4.0
      </Badge>
    );
  }
  return (
    <Badge
      variant="outline"
      className="gap-1 border-amber-300 bg-amber-50 text-[10px] font-medium text-amber-900"
    >
      <AlertTriangle className="size-3" />
      Sin licencia declarada en CKAN
    </Badge>
  );
}

function SourceCard({ source }: { source: SourceEntry }) {
  const downloaded =
    source.downloaded_at_utc !== null
      ? `Descargado ${formatUtcStamp(source.downloaded_at_utc)}`
      : `Archivo local verificado ${formatUtcStamp(source.verified_at_utc)}`;

  return (
    <article className="rounded-xl border border-border/80 bg-card px-4 py-3.5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h4 className="text-[13.5px] font-medium leading-snug text-foreground">
            {source.title}
          </h4>
          <p className="mt-0.5 font-mono text-[11.5px] text-muted-foreground">
            {source.filename} · {formatFileSize(source.bytes)}
          </p>
        </div>
        <LicenseBadge source={source} />
      </div>

      <p className="mt-1.5 text-[12.5px] text-muted-foreground">
        {source.coverage}
      </p>

      <a
        href={source.source_url}
        target="_blank"
        rel="noreferrer"
        className="mt-2 inline-flex max-w-full items-start gap-1 break-all text-[11.5px] leading-relaxed text-primary underline-offset-2 hover:underline"
      >
        <ArrowUpRight className="mt-0.5 size-3 shrink-0" />
        <span className="break-all font-mono">{source.source_url}</span>
      </a>

      <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11.5px] text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <FileSpreadsheet className="size-3" />
          {downloaded}
        </span>
        <span className="inline-flex items-center gap-1">
          <Hash className="size-3" />
          SHA-256 verificado
        </span>
      </div>

      <details className="group mt-2">
        <summary className="cursor-pointer list-none text-[12px] font-medium text-muted-foreground transition-colors hover:text-foreground">
          Ver hash, catálogo y notas
        </summary>
        <div className="mt-2 space-y-2 rounded-lg bg-muted/60 px-3 py-2.5 text-[12px] leading-relaxed text-muted-foreground">
          <p className="break-all font-mono text-[11px] text-foreground/80">
            {source.sha256}
          </p>
          <p>
            Catálogo CKAN: {source.ckan.package_title} · última modificación del
            recurso {formatUtcStamp(source.ckan.resource_last_modified_utc)}.
          </p>
          {source.notes ? <p>{source.notes}</p> : null}
          <a
            href={source.ckan.package_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 font-medium text-primary hover:underline"
          >
            Abrir conjunto de datos en datos.ine.gob.gt
            <ArrowUpRight className="size-3" />
          </a>
        </div>
      </details>
    </article>
  );
}

function Formula({ children }: { children: React.ReactNode }) {
  return (
    <code className="block rounded-lg bg-muted px-3 py-2 font-mono text-[12.5px] leading-relaxed text-foreground/90">
      {children}
    </code>
  );
}

export function SourcesDialog({ trigger }: { trigger?: React.ReactNode }) {
  const meta = basketData.meta;
  const splice = meta.splice;
  const urbana = meta.areas.Urbana;

  return (
    <Dialog>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button
            variant="outline"
            size="sm"
            aria-label="Fuentes y método"
            className="h-8 gap-1.5 rounded-full border-border/80 bg-background/70 px-2 text-xs sm:px-3"
          >
            <Database className="size-3.5" />
            <span className="hidden sm:inline">Fuentes y método</span>
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-h-[90dvh] gap-0 overflow-hidden p-0 sm:max-w-3xl">
        <DialogHeader className="border-b border-border/80 bg-card px-6 py-4">
          <DialogTitle className="flex items-center gap-2 text-[18px]">
            <Scale className="size-4 text-primary" />
            Fuentes, metodología y licencias
          </DialogTitle>
          <DialogDescription className="text-[13px]">
            Procedencia verificable de cada archivo y las reglas que aplica el
            simulador. Datos del Instituto Nacional de Estadística (INE) de
            Guatemala.
          </DialogDescription>
        </DialogHeader>

        <div className="scrollbar-thin max-h-[calc(90dvh-8.5rem)] space-y-6 overflow-y-auto px-6 py-6">
          <section className="space-y-2.5">
            <h3 className="text-[13px] font-semibold text-foreground">
              Cómo se calcula
            </h3>
            <Formula>Costo mensual per cápita = costo diario × 30 días</Formula>
            <Formula>
              Costo del hogar = costo mensual per cápita × integrantes
            </Formula>
            <Formula>
              Q por 1.000 kcal = Σ costo de alimentos con kcal &gt; 0 ÷ Σ kcal ×
              1.000
            </Formula>
            <p className="text-[13px] leading-relaxed text-muted-foreground">
              El modo por 1.000 kcal excluye el agua purificada y la sal: aportan
              costo pero 0 kcal, de modo que incluirlas atribuiría su precio a la
              energía de otros alimentos. El total mensual sí incluye todos los
              productos de la canasta.
            </p>
            <p className="text-[13px] leading-relaxed text-muted-foreground">
              La agrupación por alimento se reconstruye a partir del orden y la
              suma de kcal de la hoja de productos, porque ésta no trae la
              columna de grupo. La suma cierra exactamente contra la hoja de
              grupos del INE en kcal y difiere en menos de Q0.07 por persona y
              día en costo, por redondeo de la fuente.
            </p>
          </section>

          <Separator />

          <section className="space-y-2.5">
            <h3 className="text-[13px] font-semibold text-foreground">
              Empalme del IPC (base dic-2023 → base 2024)
            </h3>
            <p className="text-[13px] leading-relaxed text-muted-foreground">
              El INE cambió la base del IPC en enero de 2025. Comparar los índices
              publicados de ambas bases sin empalme produce una variación falsa:
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5">
                <p className="text-[10.5px] font-semibold uppercase tracking-wide text-amber-800">
                  Cálculo directo · inválido
                </p>
                <p className="mt-1 font-mono text-[15px] text-amber-950">
                  {formatSignedPercent(splice.directJan2025Monthly)}
                </p>
                <p className="mt-1 text-[11.5px] leading-relaxed text-amber-900/80">
                  {formatNumber(splice.jan2025Index2024Base, 6)} ÷{" "}
                  {formatNumber(splice.dec2024IndexDec2023Base, 6)} − 1
                </p>
              </div>
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2.5">
                <p className="text-[10.5px] font-semibold uppercase tracking-wide text-emerald-800">
                  Empalme oficial INE · enero 2025
                </p>
                <p className="mt-1 font-mono text-[15px] text-emerald-950">
                  {formatSignedPercent(splice.officialJan2025Monthly)}
                </p>
                <p className="mt-1 text-[11.5px] leading-relaxed text-emerald-900/80">
                  Factor de enlace 2023→2024:{" "}
                  {formatNumber(splice.linkFactor2023To2024, 6)}
                </p>
              </div>
            </div>
            <p className="text-[13px] leading-relaxed text-muted-foreground">
              La serie de variaciones que muestra la aplicación proviene del
              archivo <span className="font-mono">ipc_emprepu_es25.xlsx</span>,
              que ya incorpora el empalme. No se concatenan series de bases
              distintas.
            </p>
          </section>

          <Separator />

          <section className="space-y-2.5">
            <h3 className="text-[13px] font-semibold text-foreground">
              Quiebre metodológico de la canasta
            </h3>
            <p className="text-[13px] leading-relaxed text-muted-foreground">
              La CBA 2024–2026 corresponde a la actualización metodológica del
              INE a partir de la ENCOVI 2023. Sus productos, cantidades y
              requerimientos calóricos ({formatNumber(urbana.referenceKcal)}{" "}
              kcal urbanas y {formatNumber(meta.areas.Rural.referenceKcal)} kcal
              rurales por persona y día) no son comparables con las canastas
              anteriores a 2024. Por eso el simulador sólo expone enero 2024 a
              octubre 2026 y no permite construir series que crucen ese quiebre.
            </p>
          </section>

          <Separator />

          <section className="space-y-2.5">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-[13px] font-semibold text-foreground">
                Conjuntos de datos ({meta.sources.length})
              </h3>
              <span className="text-[11px] text-muted-foreground">
                Verificación: {formatUtcStamp(meta.generatedAtUtc)}
              </span>
            </div>
            <div className="space-y-2.5">
              {meta.sources.map((source) => (
                <SourceCard key={source.key} source={source} />
              ))}
            </div>
          </section>

          <Separator />

          <section className="space-y-2 text-[13px] leading-relaxed text-muted-foreground">
            <p className="flex items-start gap-2">
              <Info className="mt-0.5 size-3.5 shrink-0 text-primary" />
              <span>
                Los conjuntos del IPC declaran licencia Creative Commons
                Atribución (CC BY 4.0). El conjunto de costos de la CBA no
                declara licencia en el catálogo CKAN: se usa con atribución al
                INE como fuente y sin fines comerciales.
              </span>
            </p>
            <p>
              Los cálculos, agrupaciones y visualizaciones son elaboración propia
              del equipo participante en el Datatón INE 2026. No constituyen
              cifras oficiales del INE.
            </p>
          </section>
        </div>
      </DialogContent>
    </Dialog>
  );
}
