"use client";

import {
  ArrowDownRight,
  ArrowUpRight,
  Info,
  MapPin,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import * as React from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatNumber, formatRate, formatRatio } from "@/lib/format";
import type {
  Cell,
  Criterion,
  CriterionId,
  DeathCauses,
  LevelId,
  Metric,
  Mode,
  TopicId,
} from "@/lib/types";
import { cn } from "@/lib/utils";

type SelectedTerritory = {
  code: string;
  name: string;
  parent: string;
  population: number;
  census2018: number;
};

type Props = {
  level: LevelId;
  topicId: TopicId;
  metric: Metric;
  criterionId: CriterionId;
  criterion: Criterion;
  mode: Mode;
  territory: SelectedTerritory;
  cell: Cell | undefined;
  publicCells: Record<string, Cell>;
  deathCauses: DeathCauses;
  onShowOccurrence: () => void;
};

function rateRank(
  cells: Record<string, Cell>,
  selected: string,
): { rank: number | null; total: number } {
  const publicRates = Object.entries(cells)
    .filter(
      (entry): entry is [string, Extract<Cell, { suppressed: false }>] =>
        !entry[1].suppressed,
    )
    .map(([code, cell]) => ({ code, rate: cell.rate }))
    .sort((a, b) => b.rate - a.rate);
  const index = publicRates.findIndex((row) => row.code === selected);
  return { rank: index === -1 ? null : index + 1, total: publicRates.length };
}

export function DetailPanel({
  level,
  topicId,
  metric,
  criterionId,
  criterion,
  mode,
  territory,
  cell,
  publicCells,
  deathCauses,
  onShowOccurrence,
}: Props) {
  const available = criterion.available;
  const publicCell = cell && !cell.suppressed ? cell : null;
  const national = available ? criterion.national : null;
  const nationalRate =
    national && !national.suppressed ? national.rate : null;
  const ratio =
    publicCell && nationalRate ? publicCell.rate / nationalRate : null;
  const rank = available
    ? rateRank(publicCells, territory.code)
    : { rank: null, total: 0 };

  const causeCells =
    topicId === "deaths" && available && level === "department"
      ? deathCauses[criterionId].levels.department.cells[territory.code]
      : null;

  return (
    <Card className="overflow-hidden border-border/80 shadow-sm">
      <div className="border-b bg-muted/25 px-5 py-4">
        <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
          <MapPin className="size-3.5" />
          Territorio seleccionado
        </p>
        <div className="mt-2 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="truncate font-display text-2xl font-semibold tracking-tight">
              {territory.name}
            </h2>
            <p className="mt-0.5 truncate text-sm text-muted-foreground">
              {level === "department"
                ? "Departamento"
                : `Municipio de ${territory.parent}`}
              <span className="ml-2 rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
                {territory.code}
              </span>
            </p>
          </div>
          <Badge variant="secondary" className="shrink-0 rounded-full px-2.5 py-1 text-xs">
            {level === "department" ? "Departamental" : "Municipal"}
          </Badge>
        </div>
      </div>

      <CardContent className="space-y-5 p-5">
        {!available ? (
          <>
            <Alert className="border-amber-300/70 bg-amber-50/80 text-amber-950">
              <Info className="size-4" />
              <AlertTitle className="text-sm">
                Este indicador no existe por residencia
              </AlertTitle>
              <AlertDescription className="text-sm text-amber-900/80">
                {criterion.reason}
              </AlertDescription>
            </Alert>
            <button
              type="button"
              onClick={onShowOccurrence}
              className="w-full rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              Ver por lugar de ocurrencia
            </button>
            <PopulationStats
              population={territory.population}
              census={territory.census2018}
              nationalRate={nationalRate}
              rank={null}
              total={0}
            />
          </>
        ) : !publicCell ? (
          <>
            <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4">
              <div className="flex items-baseline gap-3">
                <span className="font-display text-5xl font-semibold leading-none text-amber-900/80">
                  —
                </span>
                <div>
                  <p className="text-sm font-semibold text-amber-950">
                    Celda suprimida
                  </p>
                  <p className="text-sm text-amber-900/75">
                    Menos de {cell?.threshold ?? 5} casos
                  </p>
                </div>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-amber-900/80">
                Por secreto estadístico no se publica el conteo ni la tasa de este
                territorio.
              </p>
            </div>
            <PopulationStats
              population={territory.population}
              census={territory.census2018}
              nationalRate={nationalRate}
              rank={null}
              total={0}
            />
            <Alert className="border-amber-300/70 bg-amber-50/60 text-amber-950">
              <ShieldAlert className="size-4" />
              <AlertTitle className="text-sm">Decreto-Ley 3-85</AlertTitle>
              <AlertDescription className="text-sm text-amber-900/80">
                Una celda con menos de {cell?.threshold ?? 5} casos no puede
                publicar números, porque la tasa permitiría reconstruir el conteo.
              </AlertDescription>
            </Alert>
          </>
        ) : (
          <>
            <div>
              <div className="flex items-baseline gap-2">
                <span className="tabular font-display text-5xl font-semibold leading-none tracking-tight">
                  {mode === "rate"
                    ? formatRate(publicCell.rate)
                    : formatNumber(publicCell.count)}
                </span>
                <span className="pb-1 text-sm text-muted-foreground">
                  {mode === "rate" ? "por 10.000 hab." : metric.unit}
                </span>
              </div>
              <p className="mt-2 text-base font-medium">{metric.label}</p>
              <p className="mt-0.5 text-sm text-muted-foreground">
                {mode === "rate"
                  ? `${formatNumber(publicCell.count)} casos en 2025`
                  : `${formatRate(publicCell.rate)} por 10.000 habitantes`}
              </p>
            </div>

            <PopulationStats
              population={territory.population}
              census={territory.census2018}
              nationalRate={nationalRate}
              rank={rank.rank}
              total={rank.total}
            />

            <div className="rounded-xl border border-border/70 bg-muted/20 p-3">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-muted-foreground">
                  Tasa frente al promedio nacional
                </span>
                <Badge
                  variant="outline"
                  className={cn(
                    "gap-0.5 border-0 px-2 py-0.5 text-xs",
                    ratio && ratio >= 1
                      ? "bg-rose-100 text-rose-800"
                      : "bg-emerald-100 text-emerald-800",
                  )}
                >
                  {ratio && ratio >= 1 ? (
                    <ArrowUpRight className="size-3.5" />
                  ) : (
                    <ArrowDownRight className="size-3.5" />
                  )}
                  {formatRatio(ratio)}
                </Badge>
              </div>
              <div className="mt-3 space-y-2">
                <ComparisonBar
                  label="Este territorio"
                  value={publicCell.rate}
                  reference={Math.max(publicCell.rate, nationalRate ?? 0)}
                  strong
                />
                <ComparisonBar
                  label="Nacional"
                  value={nationalRate}
                  reference={Math.max(publicCell.rate, nationalRate ?? 0)}
                />
              </div>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                {ratio
                  ? ratio >= 1
                    ? `La tasa es ${formatRatio(ratio)} el promedio nacional.`
                    : `La tasa equivale al ${formatNumber(ratio * 100)} % del promedio nacional.`
                  : "Sin comparación disponible."}
              </p>
            </div>

            <p className="border-l-2 border-primary/30 pl-3 text-xs leading-relaxed text-muted-foreground">
              <span className="font-semibold text-foreground">
                {criterionId === "residence"
                  ? "Lugar de residencia. "
                  : "Lugar de ocurrencia. "}
              </span>
              {criterion.note}
            </p>
          </>
        )}

        {topicId === "deaths" && available ? (
          causeCells ? (
            <CauseTable
              cells={causeCells}
              causes={deathCauses[criterionId].causes}
            />
          ) : level === "municipality" ? (
            <p className="border-t pt-4 text-xs leading-relaxed text-muted-foreground">
              El desglose por causa se publica a nivel departamental para evitar
              cruces municipio × causa con conteos pequeños.
            </p>
          ) : null
        ) : null}

        <div className="flex gap-2 border-t pt-4 text-xs leading-relaxed text-muted-foreground">
          <ShieldCheck className="mt-0.5 size-4 shrink-0 text-primary" />
          <p>
            Celdas con menos de 5 casos suprimidas; homicidios y suicidios con
            menos de 10. No se publican cortes municipio × día ni marca, color o
            modelo de vehículo.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function PopulationStats({
  population,
  census,
  nationalRate,
  rank,
  total,
}: {
  population: number;
  census: number;
  nationalRate: number | null;
  rank: number | null;
  total: number;
}) {
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-3 divide-x rounded-xl border border-border/70 bg-card">
        <Stat label="Población 2025" value={formatNumber(population)} />
        <Stat
          label="Promedio nacional"
          value={nationalRate ? formatRate(nationalRate) : "—"}
        />
        <Stat
          label="Posición por tasa"
          value={rank ? `${rank} de ${total}` : "—"}
        />
      </div>
      <p className="text-xs leading-relaxed text-muted-foreground">
        Población total proyectada por el INE para 2025. Censo 2018:{" "}
        {formatNumber(census)}; se muestra solo como referencia y nunca se usa
        como denominador.
      </p>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-3 py-2.5 text-center">
      <p className="text-xs leading-tight text-muted-foreground">{label}</p>
      <p className="tabular mt-1 text-base font-semibold leading-tight">
        {value}
      </p>
    </div>
  );
}

function ComparisonBar({
  label,
  value,
  reference,
  strong = false,
}: {
  label: string;
  value: number | null;
  reference: number;
  strong?: boolean;
}) {
  const width =
    value !== null && reference > 0
      ? Math.max(2, (value / reference) * 100)
      : 0;
  return (
    <div>
      <div className="flex items-center justify-between text-xs">
        <span
          className={
            strong ? "font-medium text-foreground" : "text-muted-foreground"
          }
        >
          {label}
        </span>
        <span className="tabular text-muted-foreground">
          {value !== null ? formatRate(value) : "—"}
        </span>
      </div>
      <div className="mt-1 h-2 overflow-hidden rounded-full bg-border/60">
        <div
          className={cn(
            "h-full rounded-full",
            strong ? "bg-primary" : "bg-muted-foreground/45",
          )}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

function CauseTable({
  cells,
  causes,
}: {
  cells: Record<"all" | "homicide" | "suicide" | "traffic", Cell>;
  causes: Record<
    "all" | "homicide" | "suicide" | "traffic",
    { label: string; threshold: number }
  >;
}) {
  const keys = ["homicide", "suicide", "traffic"] as const;
  return (
    <div className="space-y-3 border-t pt-4">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">Causas de muerte</h3>
        <span className="text-xs text-muted-foreground">Departamento</span>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="h-8 text-xs">Causa</TableHead>
            <TableHead className="h-8 text-right text-xs">Casos</TableHead>
            <TableHead className="h-8 text-right text-xs">Tasa</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {keys.map((key) => {
            const cell = cells[key];
            const publicCell = !cell.suppressed ? cell : null;
            return (
              <TableRow key={key} className="text-sm">
                <TableCell className="py-2 font-medium">
                  {causes[key].label}
                </TableCell>
                <TableCell className="tabular py-2 text-right">
                  {publicCell ? (
                    formatNumber(publicCell.count)
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs text-amber-800">
                      <ShieldAlert className="size-3" />
                      &lt; {causes[key].threshold}
                    </span>
                  )}
                </TableCell>
                <TableCell className="tabular py-2 text-right">
                  {publicCell ? formatRate(publicCell.rate) : "—"}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      <p className="text-xs leading-relaxed text-muted-foreground">
        Homicidios y suicidios usan un umbral de 10 casos; tránsito, de 5.
        Clasificación ICD-10: X85–Y09, X60–X84 y V01–V99.
      </p>
    </div>
  );
}
