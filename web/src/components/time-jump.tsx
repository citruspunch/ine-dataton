"use client";

import { CalendarRange, ChartNoAxesCombined } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { ViewId } from "@/lib/types";
import { cn } from "@/lib/utils";

interface TimeJumpProps {
  view: ViewId;
  onChange: (view: ViewId) => void;
}

export function TimeJump({ view, onChange }: TimeJumpProps) {
  const isSnapshot = view === "2024";

  return (
    <div className="flex items-center gap-2">
      <Tabs
        value={view}
        onValueChange={(next) => {
          if (next === "2024" || next === "series") onChange(next);
        }}
      >
        <TabsList
          className="h-10 rounded-full border border-border/70 bg-muted/60 p-1"
          aria-label="Salto temporal"
        >
          <TabsTrigger
            value="2024"
            title="2024 Snapshot (DINESE 2024 + Census 2018)"
            className="h-8 gap-1.5 rounded-full px-3 text-[12px] data-active:bg-card data-active:shadow-sm sm:px-4 sm:text-[13px]"
          >
            <CalendarRange className="size-3.5" />
            <span className="hidden sm:inline">Corte 2024</span>
            <span className="sm:hidden">2024</span>
          </TabsTrigger>
          <TabsTrigger
            value="series"
            title="2021–2022 Series (DINESE 2021–2022 + Census 2018)"
            className="h-8 gap-1.5 rounded-full px-3 text-[12px] data-active:bg-card data-active:shadow-sm sm:px-4 sm:text-[13px]"
          >
            <ChartNoAxesCombined className="size-3.5" />
            <span className="hidden sm:inline">Serie 2021–2022</span>
            <span className="sm:hidden">2021–22</span>
          </TabsTrigger>
        </TabsList>
      </Tabs>
      <Badge
        variant="outline"
        className={cn(
          "hidden h-6 rounded-full px-2.5 text-[10px] font-semibold tracking-wide uppercase lg:inline-flex",
          isSnapshot
            ? "border-amber-300/80 bg-amber-50 text-amber-800"
            : "border-teal-300/80 bg-teal-50 text-teal-800",
        )}
      >
        {isSnapshot ? "No comparable" : "Serie corta"}
      </Badge>
    </div>
  );
}
