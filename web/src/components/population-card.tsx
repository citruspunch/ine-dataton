"use client";

import { Card, CardContent } from "@/components/ui/card";
import { fmt, pct, percentOf } from "@/lib/format";
import type { Population } from "@/lib/types";

function Stat({
  label,
  value,
  share,
  color,
}: {
  label: string;
  value: number;
  share: number | null;
  color: string;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs text-muted-foreground">{label}</span>
        <span className="font-mono text-[13px] font-medium tabular-nums">
          {fmt(value)}
        </span>
      </div>
      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full"
          style={{ width: `${share ?? 0}%`, backgroundColor: color }}
        />
      </div>
      <div className="mt-1 text-[11.5px] text-muted-foreground">{pct(share)}</div>
    </div>
  );
}

export function PopulationCard({ population }: { population: Population }) {
  const ages = population.age_groups;
  const bands = [
    { label: "0–14", count: ages.slice(0, 3).reduce((s, a) => s + a.count, 0) },
    { label: "15–29", count: ages.slice(3, 6).reduce((s, a) => s + a.count, 0) },
    { label: "30–44", count: ages.slice(6, 9).reduce((s, a) => s + a.count, 0) },
    {
      label: "45–64",
      count: ages.slice(9, 13).reduce((s, a) => s + a.count, 0),
    },
    {
      label: "65 y más",
      count: ages.slice(13).reduce((s, a) => s + a.count, 0),
    },
  ];

  return (
    <Card className="h-full shadow-sm">
      <CardContent className="flex h-full flex-col gap-5">
        <div>
          <h2 className="text-base font-semibold tracking-tight">Población</h2>
          <p className="mt-0.5 text-[13px] text-muted-foreground">
            Censo 2018 · sexo, área y grandes grupos de edad
          </p>
        </div>

        <div className="grid grid-cols-2 gap-x-5 gap-y-4 sm:grid-cols-4">
          <Stat
            label="Hombres"
            value={population.men}
            share={percentOf(population.men, population.total)}
            color="var(--chart-4)"
          />
          <Stat
            label="Mujeres"
            value={population.women}
            share={percentOf(population.women, population.total)}
            color="var(--chart-2)"
          />
          <Stat
            label="Urbana"
            value={population.urban}
            share={percentOf(population.urban, population.total)}
            color="var(--chart-1)"
          />
          <Stat
            label="Rural"
            value={population.rural}
            share={percentOf(population.rural, population.total)}
            color="var(--chart-5)"
          />
        </div>

        <div className="space-y-3 border-t border-dashed pt-4">
          <div className="flex items-baseline justify-between">
            <span className="text-xs font-medium text-foreground">
              Distribución por edad
            </span>
            <span className="text-[11.5px] text-muted-foreground">
              {fmt(population.total)} habitantes
            </span>
          </div>
          {bands.map((band) => {
            const share = percentOf(band.count, population.total);
            return (
              <div
                key={band.label}
                className="grid grid-cols-[54px_minmax(0,1fr)_auto] items-center gap-3"
              >
                <span className="text-[12.5px] text-foreground">
                  {band.label}
                </span>
                <div className="h-2.5 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{ width: `${share ?? 0}%` }}
                  />
                </div>
                <span className="text-right font-mono text-[11.5px] tabular-nums text-muted-foreground">
                  {fmt(band.count)}
                  <span className="ml-1.5 text-[10.5px]">{pct(share)}</span>
                </span>
              </div>
            );
          })}
        </div>

        <p className="mt-auto border-t border-dashed pt-3 text-[11.5px] leading-relaxed text-muted-foreground">
          Censo 2018. No es una proyección de población a 2024.
        </p>
      </CardContent>
    </Card>
  );
}
