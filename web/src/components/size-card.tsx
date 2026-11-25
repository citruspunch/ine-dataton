"use client";

import { Card, CardContent } from "@/components/ui/card";
import { fmt, pct, percentOf } from "@/lib/format";
import type { DinesePayload, ViewId } from "@/lib/types";

interface SizeCardProps {
  view: ViewId;
  sizes: string[];
  current: DinesePayload;
  previous: DinesePayload | null;
}

export function SizeCard({ view, sizes, current, previous }: SizeCardProps) {
  const isSeries = view === "series";

  return (
    <Card className="shadow-sm">
      <CardContent className="flex h-full flex-col gap-5">
        <div>
          <h2 className="text-base font-semibold tracking-tight">
            Tamaño del establecimiento
          </h2>
          <p className="mt-0.5 text-[13px] text-muted-foreground">
            Rango de ventas declarado en DINESE · {current.year ?? 2024}
          </p>
        </div>

        <div className="space-y-4">
          {sizes.map((label, index) => {
            const value = current.size[label] ?? 0;
            const share = percentOf(value, current.total);
            const prior = previous?.size[label] ?? null;
            return (
              <div key={label}>
                <div className="flex items-baseline justify-between gap-3">
                  <span className="text-[13px] font-medium">{label}</span>
                  <span className="font-mono text-[13px] font-medium tabular-nums">
                    {fmt(value)}
                    <span className="ml-1.5 text-[11px] font-normal text-muted-foreground">
                      {pct(share)}
                    </span>
                  </span>
                </div>
                <div className="mt-1.5 h-2.5 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{
                      width: `${share ?? 0}%`,
                      opacity: 0.9 - index * 0.16,
                    }}
                  />
                </div>
                {isSeries && prior !== null ? (
                  <div className="mt-1 text-[11px] text-muted-foreground">
                    2021: {fmt(prior)}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>

        <p className="mt-auto border-t border-dashed pt-3 text-[11.5px] leading-relaxed text-muted-foreground">
          El tamaño se deriva del rango de ventas. No equivale al número de
          personas trabajadoras.
        </p>
      </CardContent>
    </Card>
  );
}
