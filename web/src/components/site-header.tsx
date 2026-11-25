"use client";

import { BarChart3 } from "lucide-react";

import { SourcesDialog } from "@/components/sources-dialog";
import { Button } from "@/components/ui/button";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-background/95 backdrop-blur-md">
      <div className="h-0.5 bg-[linear-gradient(90deg,var(--primary)_0%,var(--primary)_68%,var(--chart-2)_68%,var(--chart-2)_100%)]" />
      <div className="mx-auto flex max-w-[1180px] items-center gap-3 px-5 py-3 sm:px-6 lg:px-8">
        <div
          aria-hidden
          className="grid size-9 shrink-0 place-items-center rounded-[10px] bg-primary"
        >
          <BarChart3 className="size-[18px] text-white" strokeWidth={2.4} />
        </div>

        <div className="mr-auto min-w-0">
          <h1 className="truncate text-[16px] font-semibold leading-tight tracking-tight sm:text-[17px]">
            Canasta Básica Alimentaria
          </h1>
          <p className="mt-0.5 truncate text-[12px] leading-tight text-muted-foreground">
            <span className="sm:hidden">Costo mensual · Guatemala</span>
            <span className="hidden sm:inline">
              Simulador de costo mensual · Guatemala
            </span>
          </p>
        </div>

        <SourcesDialog
          trigger={
            <Button
              variant="ghost"
              size="sm"
              aria-label="Fuentes y método"
              className="h-9 gap-2 rounded-lg px-2.5 text-[13px] text-muted-foreground hover:text-foreground sm:px-3"
            >
              <span className="hidden sm:inline">Fuentes y método</span>
              <span className="sm:hidden">Fuentes</span>
            </Button>
          }
        />
      </div>
    </header>
  );
}
