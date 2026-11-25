import type { ReactNode } from "react";
import { AlertCircle, CalendarClock, Hash, TrendingUp } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { RangeBar } from "@/components/range-bar";
import { cn } from "@/lib/utils";
import { formatDate, formatNumber } from "@/lib/format";
import type { QueryResult } from "@/lib/types";

const badgeTone: Record<string, string> = {
  frozen: "border-amber-300/60 bg-amber-50 text-amber-800",
  current: "border-emerald-300/60 bg-emerald-50 text-emerald-800",
  limited: "border-sky-300/60 bg-sky-50 text-sky-800",
};

function StatCard({
  label,
  value,
  unit,
  hint,
  emphasis = false,
  icon,
}: {
  label: string;
  value: string;
  unit?: string;
  hint?: string;
  emphasis?: boolean;
  icon?: ReactNode;
}) {
  return (
    <Card className={cn("relative overflow-hidden border-border/80 bg-card/85", emphasis && "ring-1 ring-primary/10")}>
      <CardContent className="flex h-full flex-col justify-between gap-3 p-4">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            {label}
          </span>
          {icon ? <span className="text-muted-foreground/70">{icon}</span> : null}
        </div>
        <div>
          <div className={cn("font-mono font-semibold tabular tracking-tight", emphasis ? "text-3xl" : "text-2xl")}>
            {value}
          </div>
          {unit ? <div className="mt-0.5 text-[11px] text-muted-foreground">{unit}</div> : null}
        </div>
        {hint ? <p className="text-[10px] leading-relaxed text-muted-foreground">{hint}</p> : null}
      </CardContent>
    </Card>
  );
}

export function StatsCards({ result }: { result: QueryResult }) {
  const { stats, group, quality } = result;
  const activeMetric = stats?.metric ?? result.selectedMetric ?? "Sin métrica";
  const displayUnit =
    result.selectedUnit && stats
      ? stats.valueKind === "price"
        ? `Q · ${result.selectedUnit}`
        : result.selectedUnit
      : stats?.unit;
  const unitLabel = displayUnit ?? stats?.unit ?? "—";

  if (!stats) {
    return (
      <Card className="border-dashed border-border bg-card/70">
        <CardContent className="flex items-start gap-3 p-6">
          <AlertCircle className="mt-0.5 size-5 text-muted-foreground" aria-hidden />
          <div>
            <p className="font-medium">No hay datos válidos para este filtro.</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Pruebe otra búsqueda, amplíe las fechas o cambie de fuente. Los registros con
              fecha inválida, duplicados o sin precio no entran en los resúmenes.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
            Banda observada
          </p>
          <h2 className="mt-1 font-heading text-2xl font-semibold tracking-tight">{activeMetric}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {group.label} · {unitLabel}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className={cn("font-medium", badgeTone[group.status])}>
            {group.statusLabel}
          </Badge>
          <Badge variant="outline" className="font-normal text-muted-foreground">
            {formatNumber(stats.count)} registros válidos
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        <StatCard
          label="Mínimo"
          value={formatNumber(stats.min)}
          unit={unitLabel}
          hint="Valor más bajo observado en el filtro."
        />
        <StatCard
          label="Mediana"
          value={formatNumber(stats.median)}
          unit={unitLabel}
          emphasis
          icon={<TrendingUp className="size-4" aria-hidden />}
          hint={`P25 ${formatNumber(stats.p25)} · P75 ${formatNumber(stats.p75)}`}
        />
        <StatCard
          label="Máximo"
          value={formatNumber(stats.max)}
          unit={unitLabel}
          hint="Valor más alto; revise presentaciones y extremos."
        />
        <StatCard
          label="Registros"
          value={formatNumber(stats.count)}
          unit={`de ${formatNumber(quality.totalRecords)} en la tabla`}
          icon={<Hash className="size-4" aria-hidden />}
          hint={`${formatNumber(quality.excludedFromStats)} excluidos de los resúmenes`}
        />
        <StatCard
          label="Corte del filtro"
          value={formatDate(stats.cutoff, group.granularity)}
          unit={group.statusLabel}
          icon={<CalendarClock className="size-4" aria-hidden />}
          hint={
            group.granularity === "month"
              ? "Último mes con dato válido dentro del archivo."
              : "Última fecha de referencia con dato válido."
          }
        />
      </div>

      <div className="rounded-xl border border-border/70 bg-card/70 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2">
          <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Distribución del filtro
          </span>
          <span className="text-[10px] text-muted-foreground">
            Barra tenue = banda intercuartil (P25–P75)
          </span>
        </div>
        <RangeBar stats={stats} />
        <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
          {result.selectedUnit
            ? `Presentación seleccionada: ${result.selectedUnit}.`
            : stats.unitGroups.length > 1
              ? `Este rango combina ${stats.unitGroups.length} presentaciones o unidades. Use el filtro de presentación o busque un producto para una comparación más precisa.`
              : "Una sola presentación/unidad en el filtro actual."}
        </p>
      </div>
    </div>
  );
}
