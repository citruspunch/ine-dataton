"use client";

import {
  ArrowDownRight,
  ArrowUpRight,
  Boxes,
  Store,
  Users,
  type LucideIcon,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { fmt, pct, percentOf, signedPct } from "@/lib/format";
import type {
  DinesePayload,
  Municipality,
  Profile,
  ViewId,
} from "@/lib/types";
import { cn } from "@/lib/utils";

interface KpiCardsProps {
  view: ViewId;
  profile: Profile;
  municipality: Municipality;
  current: DinesePayload;
  previous: DinesePayload | null;
  nationalTotal: number;
}

function KpiCard({
  icon: Icon,
  label,
  value,
  children,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="py-0 shadow-sm transition-shadow hover:shadow-md">
      <CardContent className="flex h-full flex-col p-5">
        <div className="flex items-center justify-between gap-3">
          <span className="text-[13px] font-medium text-muted-foreground">
            {label}
          </span>
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary/8 text-primary">
            <Icon className="size-4" />
          </span>
        </div>
        <div className="mt-3 font-heading text-[2rem] font-semibold leading-none tracking-tight tabular-nums">
          {value}
        </div>
        <div className="mt-2 text-[12.5px] leading-relaxed text-muted-foreground">
          {children}
        </div>
      </CardContent>
    </Card>
  );
}

export function KpiCards({
  view,
  profile,
  municipality,
  current,
  previous,
  nationalTotal,
}: KpiCardsProps) {
  const year = current.year ?? (view === "2024" ? 2024 : 2022);
  const rank = municipality.ranks[String(year)];
  const share = percentOf(current.total, nationalTotal);
  const micro = current.size["Micro"] ?? 0;
  const microShare = percentOf(micro, current.total);
  const growth =
    previous && previous.total
      ? ((current.total - previous.total) / previous.total) * 100
      : null;
  const growing = growth === null || growth >= 0;
  const GrowthIcon = growing ? ArrowUpRight : ArrowDownRight;

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <KpiCard
        icon={Users}
        label="Población"
        value={fmt(profile.population.total)}
      >
        Censo 2018 · {pct(profile.population.age_summary.urban_share)} urbana
      </KpiCard>

      <KpiCard
        icon={Store}
        label={`Establecimientos · ${year}`}
        value={fmt(current.total)}
      >
        <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span>
            N.º {rank ?? "—"} de 340 · {pct(share)} del país
          </span>
          {growth !== null ? (
            <span
              className={cn(
                "inline-flex items-center gap-0.5 font-medium",
                growing ? "text-teal-700" : "text-amber-700",
              )}
            >
              <GrowthIcon className="size-3.5" />
              {signedPct(growth)} vs. 2021
            </span>
          ) : null}
        </span>
      </KpiCard>

      <KpiCard
        icon={Boxes}
        label="Microempresas"
        value={pct(microShare)}
      >
        {fmt(micro)} de {fmt(current.total)} establecimientos
      </KpiCard>
    </div>
  );
}
