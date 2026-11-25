import { AlertCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { formatDate, formatNumber } from "@/lib/format";
import type { QueryResult } from "@/lib/types";

const statusStyles: Record<string, string> = {
  frozen: "border-amber-300 bg-amber-50 text-amber-800",
  current: "border-emerald-300 bg-emerald-50 text-emerald-800",
  limited: "border-sky-300 bg-sky-50 text-sky-800",
};

function Stat({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <Card className="border-border/70 bg-card shadow-none">
      <CardContent className="flex flex-col gap-2 p-5">
        <span className="text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">
          {label}
        </span>
        <span className="font-mono text-[28px] font-semibold leading-none tracking-tight tabular">
          {value}
        </span>
        <span className="text-[13px] leading-snug text-muted-foreground">{detail}</span>
      </CardContent>
    </Card>
  );
}

export function StatsCards({ result }: { result: QueryResult }) {
  const { stats, group, quality } = result;

  if (!stats) {
    return (
      <Card className="border-dashed border-border bg-card/60 shadow-none">
        <CardContent className="flex items-start gap-3 p-6">
          <AlertCircle className="mt-0.5 size-5 text-muted-foreground" aria-hidden />
          <div>
            <p className="text-base font-medium">No hay datos para estos filtros</p>
            <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
              Pruebe otra búsqueda, amplíe las fechas o cambie de fuente. Los registros con
              alertas no entran en los resúmenes.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const unitLabel =
    result.selectedUnit && stats.valueKind === "price"
      ? `Q · ${result.selectedUnit}`
      : stats.unit;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="font-heading text-2xl font-semibold tracking-tight">{stats.metric}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {group.label} · {unitLabel}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className={cn("font-medium", statusStyles[group.status])}>
            {group.statusLabel}
          </Badge>
          <span className="text-sm text-muted-foreground">
            Corte <strong className="font-medium text-foreground">{formatDate(stats.cutoff, group.granularity)}</strong>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat
          label="Mínimo"
          value={formatNumber(stats.min)}
          detail={`${stats.unitGroups.length > 1 ? "Presentaciones combinadas" : "Valor más bajo observado"}`}
        />
        <Stat
          label="Mediana"
          value={formatNumber(stats.median)}
          detail={`P25 ${formatNumber(stats.p25)} · P75 ${formatNumber(stats.p75)}`}
        />
        <Stat
          label="Máximo"
          value={formatNumber(stats.max)}
          detail="Valor más alto observado"
        />
        <Stat
          label="Registros"
          value={formatNumber(stats.count)}
          detail={`de ${formatNumber(quality.totalRecords)} en el filtro`}
        />
      </div>

      {stats.unitGroups.length > 1 && !result.selectedUnit ? (
        <p className="text-sm text-amber-800">
          Esta banda combina {stats.unitGroups.length} presentaciones. Elija una presentación
          para comparar valores equivalentes.
        </p>
      ) : null}
    </div>
  );
}
