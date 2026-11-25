"use client";

import * as React from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from "recharts";
import { ChartLine, ChartNoAxesColumn, Info } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  type ChartConfig,
} from "@/components/ui/chart";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { areaData } from "@/lib/data";
import {
  formatKcal,
  formatNumber,
  formatPercent,
  formatQuetzales,
  formatQuetzalesCompact,
  formatPeriodShort,
  shortGroupName,
} from "@/lib/format";
import type { Area, AreaMonth, Mode } from "@/lib/types";

const MOBILE_QUERY = "(max-width: 639px)";

const MOBILE_GROUP_NAMES: Record<string, string> = {
  "Comidas y bebidas fuera del hogar": "Fuera de casa",
  "Carnes, Aves, Pescados y Huevos": "Carnes",
  "Productos alimenticios N.E.P.": "Otros",
  "Raíces y tubérculos": "Raíces",
  "Granos básicos": "Granos",
  "Pan y cereales": "Cereales",
  "Grasas y aceites": "Grasas",
  "Leche y productos lácteos": "Lácteos",
  "Bebidas no alcohólicas": "Bebidas",
  Leguminosas: "Legumbres",
  "Vegetales (verduras u hortalizas)": "Vegetales",
  Azucares: "Azúcares",
};

function subscribeMobile(callback: () => void) {
  const query = window.matchMedia(MOBILE_QUERY);
  query.addEventListener("change", callback);
  return () => query.removeEventListener("change", callback);
}

function getMobileSnapshot() {
  return window.matchMedia(MOBILE_QUERY).matches;
}

function getServerSnapshot() {
  return false;
}

type GroupChartProps = {
  area: Area;
  month: AreaMonth;
  members: number;
  mode: Mode;
};

type GroupDatum = {
  name: string;
  short: string;
  value: number;
  costPerPersonDay: number;
  costPerThousandKcal: number;
  sharePct: number;
  kcalPerPersonDay: number;
  kcalSharePct: number;
};

type TrendDatum = {
  period: string;
  shortLabel: string;
  label: string;
  value: number;
};

function GroupTooltip({
  active,
  payload,
  mode,
  members,
}: {
  active?: boolean;
  payload?: { payload?: GroupDatum }[];
  mode: Mode;
  members: number;
}) {
  if (!active || !payload?.length) return null;
  const datum = payload[0]?.payload;
  if (!datum) return null;

  return (
    <div className="min-w-[196px] rounded-lg border border-border/80 bg-card px-3 py-2.5 text-xs shadow-lg">
      <p className="font-medium leading-snug text-foreground">{datum.name}</p>
      <p className="mt-1 font-mono text-base font-semibold tabular-nums text-foreground">
        {mode === "total"
          ? formatQuetzales(datum.value)
          : `${formatQuetzales(datum.value)} / 1.000 kcal`}
      </p>
      <div className="mt-1.5 space-y-0.5 text-[10.5px] text-muted-foreground">
        {mode === "total" ? (
          <>
            <p>
              {formatPercent(datum.sharePct, 1)} del gasto mensual del hogar
            </p>
            <p>
              {formatQuetzales(datum.costPerPersonDay)} por persona y día ·{" "}
              {formatKcal(datum.kcalPerPersonDay)} por persona y día
            </p>
          </>
        ) : (
          <>
            <p>{formatPercent(datum.kcalSharePct, 1)} de las kcal de la canasta</p>
            <p>
              {formatKcal(datum.kcalPerPersonDay)} por persona y día · excluye 0
              kcal
            </p>
          </>
        )}
        {mode === "total" ? (
          <p className="pt-0.5 text-foreground/60">
            {members} {members === 1 ? "integrante" : "integrantes"} × 30 días
          </p>
        ) : null}
      </div>
    </div>
  );
}

function TrendTooltip({
  active,
  payload,
  mode,
}: {
  active?: boolean;
  payload?: { payload?: TrendDatum }[];
  mode: Mode;
}) {
  if (!active || !payload?.length) return null;
  const datum = payload[0]?.payload;
  if (!datum) return null;
  return (
    <div className="rounded-lg border border-border/80 bg-card px-3 py-2 text-xs shadow-lg">
      <p className="font-medium text-foreground">{datum.label}</p>
      <p className="mt-0.5 font-mono text-sm font-semibold tabular-nums">
        {mode === "total"
          ? formatQuetzales(datum.value)
          : `${formatQuetzales(datum.value)} / 1.000 kcal`}
      </p>
    </div>
  );
}

export function GroupChart({ area, month, members, mode }: GroupChartProps) {
  const [view, setView] = React.useState<"groups" | "trend">("groups");
  const isMobile = React.useSyncExternalStore(
    subscribeMobile,
    getMobileSnapshot,
    getServerSnapshot,
  );
  const data = areaData(area);
  const totalKcal = month.groupValues.reduce((sum, values) => sum + values[1], 0);

  const groupData: GroupDatum[] = React.useMemo(
    () =>
      month.groupValues
        .map((values, index) => {
          const name = data.groups[index] ?? `Grupo ${index + 1}`;
          const kcal = values[1];
          return {
            name,
            short: isMobile
              ? (MOBILE_GROUP_NAMES[name] ?? shortGroupName(name))
              : shortGroupName(name),
            value: mode === "total" ? values[0] * 30 * members : (values[2] ?? 0),
            costPerPersonDay: values[0],
            costPerThousandKcal: values[2] ?? 0,
            sharePct: values[3] ?? 0,
            kcalPerPersonDay: kcal,
            kcalSharePct: totalKcal > 0 ? (kcal / totalKcal) * 100 : 0,
          };
        })
        .sort((a, b) => b.value - a.value),
    [month, mode, members, data.groups, totalKcal, isMobile],
  );

  const trendData: TrendDatum[] = React.useMemo(
    () =>
      data.months.map((item) => ({
        period: item.period,
        shortLabel: formatPeriodShort(item.period),
        label: item.label,
        value:
          mode === "total"
            ? item.monthlyCostPerPerson * members
            : item.costPerThousandKcal,
      })),
    [data.months, mode, members],
  );

  const minPoint = trendData.reduce((min, item) => (item.value < min.value ? item : min));
  const maxPoint = trendData.reduce((max, item) => (item.value > max.value ? item : max));

  const chartConfig = {
    value: {
      label: mode === "total" ? "Costo mensual" : "Q por 1.000 kcal",
      color: "var(--chart-1)",
    },
  } satisfies ChartConfig;

  return (
    <Card>
      <CardHeader className="gap-2 pb-2">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle className="flex items-center gap-2 text-sm">
              {view === "groups" ? (
                <ChartNoAxesColumn className="size-4 text-primary" />
              ) : (
                <ChartLine className="size-4 text-primary" />
              )}
              {view === "groups"
                ? mode === "total"
                  ? "Costo mensual por grupo de alimentos"
                  : "Costo por 1.000 kcal según grupo"
                : mode === "total"
                  ? "Evolución del costo mensual"
                  : "Evolución del costo por 1.000 kcal"}
            </CardTitle>
            <CardDescription className="mt-0.5 text-[11px]">
              {view === "groups"
                ? mode === "total"
                  ? `Hogar de ${members} ${members === 1 ? "integrante" : "integrantes"} · ${month.label.toLowerCase()}`
                  : "Eficiencia calórica: quetzales por cada 1.000 kcal"
                : `${area} · ${formatPeriodShort(data.months[0].period)} a ${formatPeriodShort(month.period)}`}
            </CardDescription>
          </div>
          <Tabs value={view} onValueChange={(value) => setView(value as "groups" | "trend")}>
            <TabsList className="h-8">
              <TabsTrigger value="groups" className="px-2.5 text-[11px]">
                Por grupo
              </TabsTrigger>
              <TabsTrigger value="trend" className="px-2.5 text-[11px]">
                Evolución
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </CardHeader>

      <CardContent className="pb-2">
        {view === "groups" ? (
          <ChartContainer
            config={chartConfig}
            className="aspect-auto h-[420px] w-full"
          >
            <BarChart
              data={groupData}
              layout="vertical"
              margin={{ top: 4, right: 8, bottom: 0, left: 0 }}
            >
              <CartesianGrid horizontal={false} strokeDasharray="3 3" />
              <XAxis
                type="number"
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 10 }}
                tickFormatter={(value: number) => formatQuetzalesCompact(value)}
              />
              <YAxis
                type="category"
                dataKey="short"
                width={isMobile ? 100 : 150}
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: isMobile ? 9.5 : 10.5 }}
              />
              <ChartTooltip
                cursor={{ fill: "var(--muted)" }}
                content={<GroupTooltip mode={mode} members={members} />}
              />
              {mode === "kcal" ? (
                <ReferenceLine
                  x={month.costPerThousandKcal}
                  stroke="var(--chart-2)"
                  strokeDasharray="4 4"
                  strokeWidth={1.5}
                />
              ) : null}
              <Bar
                dataKey="value"
                fill="var(--color-value)"
                radius={[0, 4, 4, 0]}
                barSize={13}
              />
            </BarChart>
          </ChartContainer>
        ) : (
          <ChartContainer
            config={chartConfig}
            className="aspect-auto h-[420px] w-full"
          >
            <LineChart
              data={trendData}
              margin={{ top: 8, right: 12, bottom: 0, left: -8 }}
            >
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis
                dataKey="shortLabel"
                tickLine={false}
                axisLine={false}
                minTickGap={18}
                tick={{ fontSize: 10 }}
              />
              <YAxis
                domain={["auto", "auto"]}
                tickLine={false}
                axisLine={false}
                width={56}
                tick={{ fontSize: 10 }}
                tickFormatter={(value: number) => formatQuetzalesCompact(value)}
              />
              <ChartTooltip
                cursor={{ stroke: "var(--border)" }}
                content={<TrendTooltip mode={mode} />}
              />
              <ReferenceLine
                x={formatPeriodShort(month.period)}
                stroke="var(--chart-2)"
                strokeDasharray="4 4"
                strokeWidth={1.5}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="var(--color-value)"
                strokeWidth={2}
                dot={{ r: 1.6, fill: "var(--color-value)", strokeWidth: 0 }}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ChartContainer>
        )}
      </CardContent>

      <CardFooter className="justify-between gap-3 py-2.5 text-[10.5px] leading-snug text-muted-foreground">
        {view === "groups" ? (
          <>
            <span className="inline-flex items-start gap-1.5">
              <Info className="mt-0.5 size-3 shrink-0" />
              {mode === "total"
                ? "Agrupación derivada de la hoja de productos del INE; puede diferir del costo per cápita publicado en menos de Q0.07 por persona y día."
                : `Cada barra excluye el costo de productos con 0 kcal. La línea punteada marca el promedio de la canasta (${formatQuetzales(month.costPerThousandKcal)} por 1.000 kcal).`}
            </span>
            <span className="shrink-0 font-mono">
              {month.label}
            </span>
          </>
        ) : (
          <>
            <span>
              Mínimo {formatPeriodShort(minPoint.period)}:{" "}
              <span className="font-mono">{formatQuetzales(minPoint.value)}</span> ·
              Máximo {formatPeriodShort(maxPoint.period)}:{" "}
              <span className="font-mono">{formatQuetzales(maxPoint.value)}</span>
            </span>
            <span className="font-mono">
              {formatNumber(trendData.length)} meses
            </span>
          </>
        )}
      </CardFooter>
    </Card>
  );
}
