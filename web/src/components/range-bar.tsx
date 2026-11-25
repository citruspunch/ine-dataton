import { cn } from "@/lib/utils";
import { formatNumber } from "@/lib/format";
import type { MetricStats } from "@/lib/types";

export function RangeBar({
  stats,
  marker = null,
  compact = false,
  className,
}: {
  stats: MetricStats;
  marker?: number | null;
  compact?: boolean;
  className?: string;
}) {
  const span = stats.max - stats.min;
  const position = (value: number) => {
    if (span <= 0) return 50;
    return Math.max(0, Math.min(100, ((value - stats.min) / span) * 100));
  };

  const markerPosition = marker === null ? null : position(marker);
  const markerOutside =
    marker !== null && (marker < stats.min || marker > stats.max);

  return (
    <div className={cn("w-full", className)}>
      <div className="relative h-3">
        <div className="absolute inset-x-0 top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-muted" />
        <div
          className="absolute top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-primary/20"
          style={{
            left: `${position(stats.p25)}%`,
            width: `${Math.max(position(stats.p75) - position(stats.p25), 0.5)}%`,
          }}
          title={`Banda intercuartil: ${formatNumber(stats.p25)} a ${formatNumber(stats.p75)}`}
        />
        <div
          className="absolute top-1/2 h-3 w-0.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary"
          style={{ left: `${position(stats.median)}%` }}
          title={`Mediana: ${formatNumber(stats.median)}`}
        />
        {markerPosition !== null ? (
          <div
            className={cn(
              "absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-background shadow-sm",
              markerOutside ? "bg-destructive" : "bg-success",
            )}
            style={{ left: `${markerPosition}%` }}
            title={marker !== null ? `Valor evaluado: ${formatNumber(marker)}` : undefined}
          />
        ) : null}
      </div>
      {!compact ? (
        <div className="mt-1 flex justify-between text-[10px] text-muted-foreground">
          <span className="tabular">{formatNumber(stats.min)}</span>
          <span className="tabular font-medium text-foreground">mediana {formatNumber(stats.median)}</span>
          <span className="tabular">{formatNumber(stats.max)}</span>
        </div>
      ) : null}
    </div>
  );
}
