"use client";

import { ShieldAlert } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { PressureBadge } from "@/components/pressure-badge";
import {
  formatCurrency,
  formatIndicatorValue,
  formatInteger,
  formatPercent,
  formatRatio,
} from "@/lib/format";
import type {
  IndicatorDefinition,
  IndicatorsPayload,
  Municipality,
  PressureScore,
} from "@/lib/types";
import { cn } from "@/lib/utils";

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
      {children}
    </h3>
  );
}

function Metric({
  label,
  value,
  hint,
  suppressed,
}: {
  label: string;
  value: string;
  hint?: string;
  suppressed?: boolean;
}) {
  return (
    <div className="rounded-lg border bg-card p-3">
      <p className="text-[11px] font-medium text-muted-foreground">{label}</p>
      <p
        className={cn(
          "mt-1 text-lg font-semibold tabular-nums",
          suppressed && "text-muted-foreground",
        )}
      >
        {value}
        {suppressed ? <span className="ml-1 text-xs font-normal">§</span> : null}
      </p>
      {hint ? <p className="mt-0.5 text-[11px] text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

function PressureRow({
  definition,
  value,
  score,
}: {
  definition: IndicatorDefinition;
  value: number | null;
  score: PressureScore | undefined;
}) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{definition.short_label}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">{definition.unit}</p>
        </div>
        <PressureBadge value={score?.clase ?? "sin_dato"} />
      </div>
      <div className="mt-3 flex items-end justify-between gap-4">
        <p className="text-2xl font-semibold tabular-nums">
          {formatIndicatorValue(value, definition.format)}
        </p>
        {score?.rank_nacional ? (
          <p className="text-xs text-muted-foreground">
            Puesto <span className="font-medium text-foreground">#{score.rank_nacional}</span> de 340
          </p>
        ) : null}
      </div>
    </div>
  );
}

function countValue(
  municipality: Municipality,
  field: keyof Municipality,
): { value: string; suppressed: boolean } {
  const suppressed = municipality.campos_suprimidos.includes(String(field));
  if (suppressed) return { value: "—", suppressed: true };
  const raw = municipality[field] as number | null;
  return { value: raw === null ? "n.d." : formatInteger(raw), suppressed: false };
}

export function MunicipalitySheet({
  data,
  municipality,
  onOpenChange,
}: {
  data: IndicatorsPayload;
  municipality: Municipality | null;
  onOpenChange: (open: boolean) => void;
}) {
  const pressureDefinitions = data.pressure_indicator_keys
    .map((key) => data.indicators.find((item) => item.key === key))
    .filter((item): item is IndicatorDefinition => Boolean(item));

  const births = municipality ? countValue(municipality, "nacimientos_2025") : null;
  const deaths = municipality ? countValue(municipality, "defunciones_2025") : null;
  const under5 = municipality
    ? countValue(municipality, "defunciones_menores_5_2025")
    : null;
  const schools = municipality ? countValue(municipality, "escuelas_2022") : null;
  const students = municipality ? countValue(municipality, "estudiantes_2022") : null;

  return (
    <Sheet open={Boolean(municipality)} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-y-auto p-0 sm:max-w-xl">
        {municipality ? (
          <>
            <SheetHeader className="border-b bg-muted/30 p-6 pr-12">
              <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                {municipality.municipio_codigo} · {municipality.departamento_nombre}
              </p>
              <SheetTitle className="text-2xl tracking-tight">
                {municipality.municipio_nombre}
              </SheetTitle>
              <SheetDescription>
                Ficha municipal · corte {data.snapshot_id}
              </SheetDescription>
              <div className="flex flex-wrap gap-1.5 pt-2">
                {pressureDefinitions.map((definition) => (
                  <PressureBadge
                    key={definition.key}
                    value={municipality.presion[definition.key]?.clase ?? "sin_dato"}
                  />
                ))}
              </div>
            </SheetHeader>

            <div className="space-y-7 p-6">
              <section className="space-y-3">
                <SectionTitle>Indicadores de presión</SectionTitle>
                <div className="grid gap-2">
                  {pressureDefinitions.map((definition) => (
                    <PressureRow
                      key={definition.key}
                      definition={definition}
                      value={municipality[definition.key as keyof Municipality] as number | null}
                      score={municipality.presion[definition.key]}
                    />
                  ))}
                </div>
              </section>

              <section className="space-y-3">
                <SectionTitle>Población y hechos vitales</SectionTitle>
                <div className="grid grid-cols-2 gap-2">
                  <Metric
                    label="Población 2025"
                    value={formatInteger(municipality.poblacion_2025)}
                    hint="Proyección municipal"
                  />
                  <Metric
                    label="Población 2035"
                    value={formatInteger(municipality.poblacion_2035)}
                    hint="Proyección municipal"
                  />
                  <Metric
                    label="Crecimiento 2025–35"
                    value={formatPercent(municipality.crecimiento_poblacional_pct)}
                    hint={`${formatInteger(municipality.crecimiento_abs_2025_2035)} personas`}
                  />
                  <Metric
                    label="Nacimientos 2025"
                    value={births?.value ?? "—"}
                    hint="Residentes"
                    suppressed={births?.suppressed}
                  />
                  <Metric
                    label="Defunciones 2025"
                    value={deaths?.value ?? "—"}
                    hint="Residentes"
                    suppressed={deaths?.suppressed}
                  />
                  <Metric
                    label="Muertes <5 años 2025"
                    value={under5?.value ?? "—"}
                    hint="Sujetas a supresión si son 1–4"
                    suppressed={under5?.suppressed}
                  />
                </div>
              </section>

              <section className="space-y-3">
                <SectionTitle>Servicios educativos</SectionTitle>
                <div className="grid grid-cols-2 gap-2">
                  <Metric
                    label="Escuelas 2022"
                    value={schools?.value ?? "—"}
                    hint="Establecimientos únicos"
                    suppressed={schools?.suppressed}
                  />
                  <Metric
                    label="Estudiantes 2022"
                    value={students?.value ?? "—"}
                    hint="Matrícula total"
                    suppressed={students?.suppressed}
                  />
                  <Metric
                    label="Nacimientos por escuela"
                    value={formatRatio(municipality.nacimientos_por_escuela_2025)}
                    hint="2025 / 2022"
                  />
                  <Metric
                    label="Estudiantes por escuela"
                    value={formatRatio(municipality.estudiantes_por_escuela_2022)}
                    hint="Matrícula 2022"
                  />
                </div>
              </section>

              <section className="space-y-3">
                <SectionTitle>Pobreza y recursos</SectionTitle>
                <div className="grid grid-cols-2 gap-2">
                  <Metric
                    label="Pobreza general 2023"
                    value={formatPercent(municipality.pobreza_general_pct_2023)}
                  />
                  <Metric
                    label="Pobreza extrema 2023"
                    value={formatPercent(municipality.pobreza_extrema_pct_2023)}
                    hint={municipality.pobreza_extrema_pct_2023 === null ? "No publicada" : undefined}
                  />
                  <Metric
                    label="Asignación 2026"
                    value={formatCurrency(municipality.asignacion_constitucional_2026_gtq, 0)}
                    hint="Situado constitucional"
                  />
                  <Metric
                    label="Asignación por habitante"
                    value={formatCurrency(municipality.asignacion_por_habitante_2026_gtq)}
                    hint="Cálculo oficial"
                  />
                  <Metric
                    label="Ingresos propios por habitante"
                    value={formatCurrency(municipality.ingresos_propios_per_capita_2024_gtq)}
                    hint="2024"
                  />
                  <Metric
                    label="Consumo promedio"
                    value={formatCurrency(municipality.consumo_promedio_q_mes_2023)}
                    hint="Q por persona al mes, 2023"
                  />
                </div>
              </section>

              {municipality.campos_suprimidos.length ? (
                <section className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-amber-950 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-50">
                  <div className="flex items-start gap-2">
                    <ShieldAlert className="mt-0.5 size-4 shrink-0" />
                    <div>
                      <p className="text-sm font-medium">Celdas suprimidas</p>
                      <p className="mt-1 text-xs leading-relaxed">
                        Por secreto estadístico no se publican estos valores (conteos 1–4 o tasas
                        derivadas):
                      </p>
                      <ul className="mt-2 list-disc space-y-0.5 pl-4 text-xs">
                        {municipality.campos_suprimidos.map((field) => (
                          <li key={field}>{data.suppression.labels[field] ?? field}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </section>
              ) : null}

              <p className="text-[11px] leading-relaxed text-muted-foreground">
                Fuente: INE, MINEDUC y SEGEPLAN. Consulte la pestaña «Datos y fuentes» para ver la
                URL, la fecha UTC de descarga y la licencia de cada serie. Esta herramienta no es
                un sistema oficial del INE.
              </p>
            </div>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
