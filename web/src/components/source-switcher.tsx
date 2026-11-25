"use client";

import { ArrowUpRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatCompact, formatDate, statusTone } from "@/lib/format";
import type { SourceGroup, Summary } from "@/lib/types";

const accentBar: Record<SourceGroup, string> = {
  DPIR: "bg-chart-2",
  IPMC: "bg-chart-1",
  ICC: "bg-chart-3",
  BASKETS: "bg-chart-4",
};

const badgeStyles: Record<string, string> = {
  frozen: "border-amber-300/60 bg-amber-50 text-amber-800",
  current: "border-emerald-300/60 bg-emerald-50 text-emerald-800",
  limited: "border-sky-300/60 bg-sky-50 text-sky-800",
};

export function SourceSwitcher({
  summary,
  active,
  onChange,
}: {
  summary: Summary;
  active: SourceGroup;
  onChange: (source: SourceGroup) => void;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {summary.order.map((group) => {
        const info = summary.groups[group];
        const isActive = group === active;
        return (
          <button
            key={group}
            type="button"
            onClick={() => onChange(group)}
            aria-pressed={isActive}
            className={cn(
              "group relative overflow-hidden rounded-xl border bg-card/80 p-4 text-left transition-all",
              "hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md",
              isActive
                ? "border-primary/35 shadow-md ring-1 ring-primary/20"
                : "border-border/80",
            )}
          >
            <span className={cn("absolute inset-x-0 top-0 h-1", accentBar[group])} />
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-heading text-lg font-semibold">{info.shortLabel}</span>
                  <Badge
                    variant="outline"
                    className={cn("h-5 px-1.5 text-[9px] font-semibold uppercase tracking-wide", badgeStyles[info.status])}
                  >
                    {statusTone(info.status) === "warning"
                      ? "Congelado"
                      : info.status === "limited"
                        ? "Parcial"
                        : "Vigente"}
                  </Badge>
                </div>
                <p className="mt-1 text-xs font-medium text-foreground/80">{info.label}</p>
              </div>
              <ArrowUpRight
                className={cn(
                  "size-4 shrink-0 text-muted-foreground transition-transform",
                  isActive ? "text-primary" : "group-hover:-translate-y-0.5 group-hover:translate-x-0.5",
                )}
                aria-hidden
              />
            </div>
            <p className="mt-3 line-clamp-2 min-h-8 text-xs leading-relaxed text-muted-foreground">
              {info.tagline}
            </p>
            <div className="mt-3 flex items-center justify-between border-t border-border/70 pt-2.5 text-[11px]">
              <span className="text-muted-foreground">
                {formatCompact(info.recordCount)} registros
              </span>
              <span className="font-medium tabular">
                {formatDate(info.cutoff, info.granularity)}
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
