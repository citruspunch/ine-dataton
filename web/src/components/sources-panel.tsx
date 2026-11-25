"use client";

import * as React from "react";
import {
  ChevronDown,
  Database,
  Download,
  ExternalLink,
  FileCheck2,
  Info,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  formatBytes,
  formatDateUtc,
  formatInteger,
  formatUtc,
  licenseBadgeClass,
} from "@/lib/format";
import type { IndicatorsPayload, SourceRecord } from "@/lib/types";
import { cn } from "@/lib/utils";

function licenseShortLabel(source: SourceRecord): string {
  switch (source.license.id) {
    case "cc-nc":
      return "CC BY-NC 2.0";
    case "cc-zero":
      return "CC0 1.0";
    case "odc-by":
      return "ODC-By";
    case "cc-by":
      return "CC BY";
    case "ine-no-declarada":
    case "ine-fuente-institucional":
      return "No declarada";
    default:
      return source.license.id;
  }
}

function Stat({ label, value, hint }: { label: string; value: React.ReactNode; hint?: string }) {
  return (
    <div className="rounded-lg border bg-muted/20 p-3">
      <div className="text-[11px] font-medium text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold tabular-nums">{value}</div>
      {hint ? <div className="mt-0.5 text-[11px] leading-snug text-muted-foreground">{hint}</div> : null}
    </div>
  );
}

function downloadStatusLabel(status: string | null): string {
  switch (status) {
    case "downloaded":
      return "descargado";
    case "cached":
      return "en caché";
    case "local_cache":
      return "caché local";
    case "derived":
      return "derivado";
    default:
      return status ?? "—";
  }
}

function SourceRow({
  source,
  expanded,
  onToggle,
}: {
  source: SourceRecord;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={expanded}
        className="grid w-full grid-cols-[1fr_auto] items-center gap-4 px-5 py-4 text-left transition-colors hover:bg-muted/40 focus-visible:bg-muted/40 focus-visible:outline-none"
      >
        <div className="min-w-0">
          <p className="line-clamp-2 text-sm font-medium leading-snug text-foreground">
            {source.title}
          </p>
          <p className="mt-0.5 truncate text-xs text-muted-foreground">{source.publisher}</p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          <Badge
            variant="outline"
            className={cn(
              "whitespace-nowrap text-[10px]",
              licenseBadgeClass(source.license.id, source.non_commercial),
            )}
          >
            {licenseShortLabel(source)}
          </Badge>
          <span className="hidden text-xs text-muted-foreground md:inline">
            {formatDateUtc(source.downloaded_at_utc)}
          </span>
          <ChevronDown
            className={cn(
              "size-4 shrink-0 text-muted-foreground transition-transform",
              expanded && "rotate-180",
            )}
          />
        </div>
      </button>

      {expanded ? (
        <div className="space-y-4 border-t bg-muted/20 px-5 py-4 text-xs">
          <p className="text-muted-foreground">{source.description}</p>
          <dl className="space-y-3">
            <div>
              <dt className="font-medium text-foreground">Descarga</dt>
              <dd className="mt-0.5">
                <a
                  href={source.download_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-start gap-1 text-primary underline-offset-2 hover:underline"
                >
                  <span className="break-all">{source.download_url}</span>
                  <ExternalLink className="mt-0.5 size-3 shrink-0" />
                </a>
              </dd>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <dt className="font-medium text-foreground">Descarga UTC</dt>
                <dd className="mt-0.5 font-mono text-[11px]">
                  {formatUtc(source.downloaded_at_utc)}
                </dd>
              </div>
              <div>
                <dt className="font-medium text-foreground">Estado</dt>
                <dd className="mt-0.5">
                  {downloadStatusLabel(source.download_status)} · {formatBytes(source.bytes)} ·{" "}
                  {source.format.toUpperCase()}
                </dd>
              </div>
            </div>
            <div>
              <dt className="font-medium text-foreground">Página del conjunto</dt>
              <dd className="mt-0.5">
                <a
                  href={source.dataset_page}
                  target="_blank"
                  rel="noreferrer"
                  className="text-primary underline-offset-2 hover:underline"
                >
                  Abrir fuente original
                </a>
              </dd>
            </div>
            <div>
              <dt className="font-medium text-foreground">SHA-256</dt>
              <dd className="mt-0.5">
                <code className="block break-all rounded bg-background px-2 py-1 font-mono text-[10px]">
                  {source.sha256 ?? "—"}
                </code>
              </dd>
            </div>
            <div>
              <dt className="font-medium text-foreground">Licencia y atribución</dt>
              <dd className="mt-0.5 leading-relaxed text-muted-foreground">
                {source.license.name}. CKAN:{" "}
                <span className="font-mono">{source.ckan_license_id ?? "no declarada"}</span>.{" "}
                {source.attribution}.
              </dd>
            </div>
          </dl>
          {source.non_commercial ? (
            <p className="rounded-md border border-rose-200 bg-rose-50 p-2 text-[11px] text-rose-900 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-100">
              <strong>Uso no comercial.</strong> Se requiere atribución a SEGEPLAN. Cualquier
              reutilización comercial necesita autorización expresa.
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function SourcesPanel({ data }: { data: IndicatorsPayload }) {
  const [expanded, setExpanded] = React.useState<string | null>(null);
  const suppressedFields = data.suppression.counts.count_fields.filter(
    (field) => field.suppressed_cells > 0,
  );
  const derivedFields = data.suppression.derived.derived_fields.filter(
    (field) => field.suppressed_cells > 0,
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Datos y fuentes</h2>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            Cada archivo se guarda localmente. Si falta, el pipeline lo descarga desde la URL
            exacta, registra fecha UTC y SHA-256, y lo reutiliza en las siguientes ejecuciones.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline" size="sm">
            <a href="/data/indicators.json" download>
              <Download className="size-3.5" /> JSON
            </a>
          </Button>
          <Button asChild variant="outline" size="sm">
            <a href="/data/provenance.json" download>
              <Download className="size-3.5" /> Procedencia
            </a>
          </Button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-rose-200 bg-rose-50/60 p-4 dark:border-rose-900/60 dark:bg-rose-950/20">
          <Badge
            variant="outline"
            className="border-rose-300 bg-white/60 text-rose-800 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-200"
          >
            CC BY-NC 2.0
          </Badge>
          <p className="mt-3 text-sm font-semibold text-rose-950 dark:text-rose-50">
            SEGEPLAN · no comercial
          </p>
          <p className="mt-1 text-xs leading-relaxed text-rose-900/80 dark:text-rose-100/80">
            Atribución requerida. Uso comercial solo con autorización expresa.
          </p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-4 dark:border-emerald-900/60 dark:bg-emerald-950/20">
          <Badge
            variant="outline"
            className="border-emerald-300 bg-white/60 text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-200"
          >
            CC0 1.0
          </Badge>
          <p className="mt-3 text-sm font-semibold text-emerald-950 dark:text-emerald-50">
            MINEDUC · reutilización libre
          </p>
          <p className="mt-1 text-xs leading-relaxed text-emerald-900/80 dark:text-emerald-100/80">
            Sin restricciones adicionales. Se cita igualmente al MINEDUC como fuente.
          </p>
        </div>
        <div className="rounded-xl border bg-muted/30 p-4">
          <Badge variant="outline" className="bg-background">
            Según recurso
          </Badge>
          <p className="mt-3 text-sm font-semibold">INE · condiciones de la fuente</p>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
            ODC-By cuando está declarada; los recursos sin licencia CKAN se citan sin atribuir una
            licencia abierta.
          </p>
        </div>
      </div>

      <Card className="gap-0 py-0">
        <CardHeader className="border-b px-5 py-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Database className="size-4" /> Archivos utilizados
          </CardTitle>
          <CardDescription>
            {data.sources.length} series · haga clic en una fila para ver URL, licencia, fecha y
            hash.
          </CardDescription>
        </CardHeader>
        <CardContent className="divide-y p-0">
          {data.sources.map((source) => (
            <SourceRow
              key={source.id}
              source={source}
              expanded={expanded === source.id}
              onToggle={() => setExpanded((current) => (current === source.id ? null : source.id))}
            />
          ))}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FileCheck2 className="size-4" /> Calidad de los cruces
            </CardTitle>
            <CardDescription>Verificaciones ejecutadas por el pipeline.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <Stat
              label="Municipios"
              value="340 / 340"
              hint="Sin códigos descartados"
            />
            <Stat
              label="Cruce +21"
              value="16"
              hint="Municipios de Guatemala"
            />
            <Stat
              label="Traslape 2015–2030"
              value={`${data.data_quality.projection_overlap.max_abs_difference_people} personas`}
              hint="Diferencia máxima"
            />
            <Stat
              label="Pobreza extrema"
              value={`${data.data_quality.segeplan.poverty_2023.missing_extreme_poverty} sin dato`}
              hint="No se imputan como cero"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <ShieldCheck className="size-4" /> Supresión estadística
            </CardTitle>
            <CardDescription>Conteos pequeños y tasas derivadas.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <Stat label="Umbral" value={`< ${data.suppression.threshold}`} hint="Conteos 1–4" />
              <Stat
                label="Celdas suprimidas"
                value={formatInteger(data.suppression.total_suppressed_cells)}
                hint={`${data.suppression.counts.municipalities_with_suppression} municipios`}
              />
            </div>
            <div className="space-y-1 text-xs text-muted-foreground">
              {suppressedFields.map((field) => (
                <div key={field.field} className="flex justify-between gap-3">
                  <span>{field.label}</span>
                  <span className="font-mono">{field.suppressed_cells}</span>
                </div>
              ))}
              {derivedFields.map((field) => (
                <div key={field.field} className="flex justify-between gap-3">
                  <span>{field.label} (tasa derivada)</span>
                  <span className="font-mono">{field.suppressed_cells}</span>
                </div>
              ))}
            </div>
            <p className="rounded-md border bg-muted/30 p-2 text-[11px] leading-relaxed text-muted-foreground">
              <strong>Base legal:</strong> {data.suppression.legal_basis} El umbral 5 es una
              salvaguarda conservadora del prototipo, no una marca oficial del INE.
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Info className="size-4" /> Limitaciones
            </CardTitle>
            <CardDescription>Lo que esta comparación no puede decir.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-muted-foreground">
              {data.limitations.slice(0, 5).map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
            <details className="mt-3 text-xs text-muted-foreground">
              <summary className="cursor-pointer font-medium text-foreground">
                Ver todas las limitaciones
              </summary>
              <ul className="mt-2 list-disc space-y-2 pl-5">
                {data.limitations.slice(5).map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </details>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Sparkles className="size-4" /> Uso de IA
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm leading-relaxed text-muted-foreground">
              {data.ai_disclosure}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Cómo citar</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs leading-relaxed text-muted-foreground">
              <p>INE, Guatemala. Proyecciones municipales y estadísticas vitales 2025.</p>
              <p>MINEDUC, Guatemala. Establecimientos y estudiantes 2021–2022. CC0 1.0.</p>
              <p>SEGEPLAN. Pobreza municipal 2023 y asignación constitucional 2026. CC BY-NC 2.0.</p>
              <p className="rounded border bg-muted/30 p-2">
                Herramienta independiente del Datatón INE 2026. No es un sistema oficial del INE ni
                un producto interinstitucional.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
