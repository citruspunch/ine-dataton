"use client";

import { ChartNoAxesColumnIncreasing } from "lucide-react";

import { SourcesDialog } from "@/components/sources-dialog";
import { Badge } from "@/components/ui/badge";
import { basketData } from "@/lib/data";

function BrandMark() {
  return (
    <div
      aria-hidden
      className="grid size-10 place-items-center rounded-xl bg-primary shadow-[inset_0_-2px_0_0_rgba(0,0,0,0.12)]"
    >
      <ChartNoAxesColumnIncreasing className="size-5 text-white" strokeWidth={2.4} />
    </div>
  );
}

export function SiteHeader() {
  const meta = basketData.meta;

  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-background/95 backdrop-blur-md supports-[backdrop-filter]:bg-background/90">
      <div className="h-1 bg-[linear-gradient(90deg,var(--primary)_0%,var(--primary)_62%,var(--chart-2)_62%,var(--chart-2)_100%)]" />
      <div className="mx-auto flex max-w-[1440px] flex-wrap items-center gap-x-3.5 gap-y-2 px-4 py-2.5 sm:px-6 lg:px-8">
        <BrandMark />
        <div className="mr-auto min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-primary">
            Datatón INE 2026 · Datos abiertos
          </p>
          <div className="flex flex-wrap items-baseline gap-x-2.5 gap-y-0.5">
            <h1 className="truncate text-[15px] font-semibold leading-tight tracking-tight sm:text-base">
              Canasta Básica Alimentaria
            </h1>
            <span className="hidden text-xs text-muted-foreground sm:inline">
              Simulador de costo mensual · {meta.period.firstLabel} –{" "}
              {meta.period.lastLabel}
            </span>
          </div>
        </div>

        <Badge
          variant="outline"
          className="hidden border-border/80 bg-card text-[10px] font-medium text-muted-foreground md:inline-flex"
        >
          CBA urbana y rural · 2024–2026
        </Badge>
        <SourcesDialog />
      </div>
    </header>
  );
}
