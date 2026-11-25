"use client";

import * as React from "react";
import {
  Bar,
  BarChart,
  LabelList,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartContainer, type ChartConfig } from "@/components/ui/chart";
import { PRESSURE_CLASS_STYLES, formatIndicatorValue } from "@/lib/format";
import type {
  IndicatorDefinition,
  IndicatorsPayload,
  Municipality,
  PressureClass,
} from "@/lib/types";
import { cn } from "@/lib/utils";
import { ArrowUpRight } from "lucide-react";

type ChartRow = {
  codigo: string;
  label: string;
  municipio: string;
  departamento: string;
  value: number;
  clase: PressureClass;
  rank: number | null;
};

const TOP_N = 10;

function buildRows(
  data: IndicatorsPayload,
  department: string,
  indicatorKey: string,
  definition: IndicatorDefinition,
): { rows: ChartRow[]; total: number } {
  const inDepartment =
    department === "all"
      ? data.municipalities
      : data.municipalities.filter((m) => m.departamento_codigo === department);

  const candidates: ChartRow[] = inDepartment
    .map((m: Municipality) => {
      const value = m[indicatorKey as keyof Municipality] as number | null;
      if (value === null || value === undefined || Number.isNaN(value)) return null;
      const score = m.presion[indicatorKey];
      return {
        codigo: m.municipio_codigo,
        label: m.municipio_nombre,
        municipio: m.municipio_nombre,
        departamento: m.departamento_nombre,
        value,
        clase: (score?.clase ?? "sin_dato") as PressureClass,
        rank: score?.rank_nacional ?? null,
      } satisfies ChartRow;
    })
    .filter((row): row is ChartRow => row !== null);

  candidates.sort((a, b) =>
    definition.direction === "lower" ? a.value - b.value : b.value - a.value,
  );

  return { rows: candidates.slice(0, TOP_N), total: candidates.length };
}

function TooltipCard({
  active,
  payload,
  definition,
}: {
  active?: boolean;
  payload?: Array<{ payload?: ChartRow }>;
  definition: IndicatorDefinition;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload;
  if (!row) return null;
  return (
    <div className="max-w-xs rounded-xl border bg-popover p-3 text-sm shadow-xl">
      <p className="font-semibold text-popover-foreground">{row.municipio}</p>
      <p className="text-xs text-muted-foreground">{row.departamento}</p>
      <div className="mt-3 flex items-center justify-between gap-4">
        <span className="text-xs text-muted-foreground">{definition.short_label}</span>
        <span className="font-mono font-semibold tabular-nums">
          {formatIndicatorValue(row.value, definition.format)}
        </span>
      </div>
      {row.rank !== null ? (
        <p className="mt-1 text-xs text-muted-foreground">
          Puesto <span className="font-medium text-foreground">#{row.rank}</span> de 340
        </p>
      ) : null}
    </div>
  );
}

export function IndicatorChart({
  data,
  department,
  indicatorKey,
  onShowSources,
}: {
  data: IndicatorsPayload;
  department: string;
  indicatorKey: string;
  onShowSources?: () => void;
}) {
  const definition = data.indicators.find((item) => item.key === indicatorKey);
  const { rows, total } = React.useMemo(
    () => (definition ? buildRows(data, department, indicatorKey, definition) : { rows: [], total: 0 }),
    [data, department, indicatorKey, definition],
  );

  if (!definition) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        Indicador no disponible.
      </div>
    );
  }

  const departmentName =
    department === "all"
      ? "Todos los departamentos"
      : data.departments.find((item) => item.codigo === department)?.nombre ?? "Departamento";
  const scope =
    department === "all"
      ? "Top 10 nacional"
      : `${departmentName} · ${rows.length} de ${total} municipios`;
  const height = Math.max(260, rows.length * 46 + 12);
  const maxValue = rows.length ? Math.max(...rows.map((row) => row.value)) : 0;
  const config: ChartConfig = {
    value: { label: definition.short_label, color: "var(--chart-1)" },
  };

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold tracking-tight">Ranking de presión</h2>
          <p className="mt-1 text-sm text-muted-foreground">{scope}</p>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            {definition.description}
          </p>
        </div>
      </div>

      {rows.length === 0 ? (
        <div className="mt-6 flex h-64 items-center justify-center rounded-xl border border-dashed text-sm text-muted-foreground">
          No hay valores disponibles para este indicador.
        </div>
      ) : (
        <>
          <div className="mt-5 space-y-1 sm:hidden">
            {rows.map((row, index) => (
              <div key={row.codigo} className="rounded-lg px-1 py-2">
                <div className="flex items-center gap-2">
                  <span className="w-5 shrink-0 text-right font-mono text-[11px] text-muted-foreground">
                    {index + 1}
                  </span>
                  <span
                    className={cn(
                      "size-1.5 shrink-0 rounded-full",
                      PRESSURE_CLASS_STYLES[row.clase]?.dot ??
                        PRESSURE_CLASS_STYLES.sin_dato.dot,
                    )}
                  />
                  <span className="min-w-0 flex-1 truncate text-sm font-medium">
                    {row.municipio}
                  </span>
                  <span className="shrink-0 font-mono text-sm tabular-nums">
                    {formatIndicatorValue(row.value, definition.format)}
                  </span>
                </div>
                <div className="mt-1.5 flex items-center gap-2 pl-7">
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{
                        width: `${maxValue > 0 ? Math.max(4, (row.value / maxValue) * 100) : 0}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <ChartContainer
            config={config}
            className="mt-4 hidden aspect-auto w-full sm:flex"
            style={{ height }}
          >
            <BarChart
              data={rows}
              layout="vertical"
              margin={{ top: 0, right: 58, bottom: 0, left: 0 }}
              barCategoryGap={10}
            >
              <XAxis type="number" hide domain={[0, "dataMax"]} />
              <YAxis
                type="category"
                dataKey="label"
                width={152}
                tickLine={false}
                axisLine={false}
                tickMargin={10}
                fontSize={12}
                tick={{ fill: "var(--foreground)" }}
                tickFormatter={(value: string) =>
                  value.length > 23 ? `${value.slice(0, 22)}…` : value
                }
              />
              <Tooltip
                cursor={{ fill: "var(--muted)", opacity: 0.6 }}
                content={<TooltipCard definition={definition} />}
              />
              <Bar
                dataKey="value"
                fill="var(--chart-1)"
                radius={[0, 7, 7, 0]}
                barSize={18}
                isAnimationActive={false}
              >
                <LabelList
                  dataKey="value"
                  position="right"
                  offset={8}
                  fontSize={12}
                  fill="var(--muted-foreground)"
                  formatter={(value) => {
                    const numeric = typeof value === "number" ? value : Number(value);
                    return formatIndicatorValue(numeric, definition.format);
                  }}
                />
              </Bar>
            </BarChart>
          </ChartContainer>

          <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
            <span>
              Barras más largas = mayor presión relativa.{" "}
              {total > rows.length
                ? `Se muestran los ${rows.length} primeros de ${total}; la tabla incluye todos.`
                : `${total} municipios con dato.`}
            </span>
            {onShowSources ? (
              <button
                type="button"
                onClick={onShowSources}
                className="inline-flex items-center gap-1 font-medium text-foreground underline-offset-4 hover:underline"
              >
                Fuente: INE · MINEDUC · SEGEPLAN
                <ArrowUpRight className="size-3" />
              </button>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}
