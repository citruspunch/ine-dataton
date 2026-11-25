"use client";

import { CalendarRange, Flag, RotateCcw, Search, SlidersHorizontal, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { CountFacet, SourceGroup } from "@/lib/types";

const sourceOptions: Array<{ value: SourceGroup; label: string }> = [
  { value: "DPIR", label: "DPIR · Precios de referencia" },
  { value: "IPMC", label: "IPMC · Materiales de construcción" },
  { value: "ICC", label: "ICC · Costo de construcción" },
  { value: "BASKETS", label: "CBAU / CBAR · Canastas básicas" },
];

const quickQueries: Record<SourceGroup, string[]> = {
  DPIR: ["papel bond", "guantes", "oxígeno", "arroz", "combustible"],
  IPMC: ["cemento", "acero", "madera", "tubería", "pintura"],
  ICC: ["materiales", "mano de obra", "cimentación", "cubierta"],
  BASKETS: ["arroz", "tortillas", "pollo", "frijol", "leche"],
};

export function Filters({
  source,
  q,
  from,
  to,
  metric,
  unit,
  flaggedOnly,
  metrics,
  units,
  suggestions,
  onChange,
  onClear,
}: {
  source: SourceGroup;
  q: string;
  from: string;
  to: string;
  metric: string;
  unit: string;
  flaggedOnly: boolean;
  metrics: CountFacet[];
  units: CountFacet[];
  suggestions: string[];
  onChange: (patch: {
    source?: SourceGroup;
    q?: string;
    from?: string;
    to?: string;
    metric?: string;
    unit?: string;
    flagged?: boolean;
  }) => void;
  onClear: () => void;
}) {
  const hasFilters = Boolean(q || from || to || unit || flaggedOnly);
  const showUnitSelect = units.length > 1 && units.length <= 40;
  const tooManyUnits = units.length > 40;

  return (
    <div className="rounded-2xl border border-border/80 bg-card/85 p-4 shadow-sm backdrop-blur sm:p-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
        <div className="min-w-0 flex-1">
          <Label htmlFor="search" className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Buscar producto, material o categoría
          </Label>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
            <Input
              id="search"
              list="item-suggestions"
              value={q}
              onChange={(event) => onChange({ q: event.target.value })}
              placeholder="Ej. cemento gris, varilla 3/8, papel bond, arroz…"
              className="h-11 rounded-xl border-border/90 bg-background/70 pl-9 pr-9 text-[15px] shadow-xs"
              autoComplete="off"
            />
            {q ? (
              <button
                type="button"
                onClick={() => onChange({ q: "" })}
                aria-label="Limpiar búsqueda"
                className="absolute right-2.5 top-1/2 grid size-6 -translate-y-1/2 place-items-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <X className="size-3.5" aria-hidden />
              </button>
            ) : null}
          </div>
          <datalist id="item-suggestions">
            {suggestions.map((item) => (
              <option key={item} value={item} />
            ))}
          </datalist>
        </div>

        <div className="w-full lg:w-[265px]">
          <Label className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            <SlidersHorizontal className="size-3" aria-hidden />
            Fuente
          </Label>
          <Select value={source} onValueChange={(value) => onChange({ source: value as SourceGroup })}>
            <SelectTrigger className="h-11 w-full rounded-xl border-border/90 bg-background/70">
              <SelectValue placeholder="Seleccione una fuente">
                {sourceOptions.find((option) => option.value === source)?.label ?? "Fuente"}
              </SelectValue>
            </SelectTrigger>
            <SelectContent>
              {sourceOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button
          type="button"
          variant="outline"
          onClick={onClear}
          disabled={!hasFilters && !q}
          className={cn("h-11 shrink-0 gap-1.5 rounded-xl", !hasFilters && !q && "opacity-50")}
        >
          <RotateCcw className="size-3.5" aria-hidden />
          Limpiar
        </Button>
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <Label htmlFor="from" className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            <CalendarRange className="size-3" aria-hidden />
            Desde
          </Label>
          <Input
            id="from"
            type="month"
            value={from}
            onChange={(event) => onChange({ from: event.target.value })}
            className="h-10 rounded-xl border-border/90 bg-background/70"
          />
        </div>
        <div>
          <Label htmlFor="to" className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            <CalendarRange className="size-3" aria-hidden />
            Hasta
          </Label>
          <Input
            id="to"
            type="month"
            value={to}
            onChange={(event) => onChange({ to: event.target.value })}
            className="h-10 rounded-xl border-border/90 bg-background/70"
          />
        </div>

        {metrics.length > 1 ? (
          <div>
            <Label className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Métrica
            </Label>
            <Select value={metric} onValueChange={(value) => onChange({ metric: value })}>
              <SelectTrigger className="h-10 w-full rounded-xl border-border/90 bg-background/70">
                <SelectValue placeholder="Métrica">
                  {metrics.find((option) => option.value === metric)?.label ?? metric ?? "Métrica"}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {metrics.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label} · {option.count}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ) : (
          <div>
            <Label className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
              Métrica
            </Label>
            <div className="flex h-10 items-center rounded-xl border border-border/70 bg-muted/40 px-3 text-sm text-muted-foreground">
              {metric || "Automática"}
            </div>
          </div>
        )}

        <div>
          <Label className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Presentación / unidad
          </Label>
          {showUnitSelect ? (
            <Select value={unit || "__all__"} onValueChange={(value) => onChange({ unit: value === "__all__" ? "" : value })}>
              <SelectTrigger className="h-10 w-full rounded-xl border-border/90 bg-background/70">
                <SelectValue placeholder="Todas">
                  {unit || `Todas (${units.length})`}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">Todas ({units.length})</SelectItem>
                {units.map((option) => (
                  <SelectItem key={option.value} value={option.label}>
                    {option.label} · {option.count}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <div className="flex h-10 items-center rounded-xl border border-dashed border-border/70 bg-muted/30 px-3 text-xs text-muted-foreground">
              {tooManyUnits
                ? "Escriba un producto para acotar"
                : unit || units[0]?.label || "Una sola presentación"}
            </div>
          )}
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Button
          type="button"
          size="sm"
          variant={flaggedOnly ? "default" : "outline"}
          onClick={() => onChange({ flagged: !flaggedOnly })}
          className="h-8 gap-1.5 rounded-full text-xs"
        >
          <Flag className="size-3" aria-hidden />
          Solo registros con alertas
        </Button>
        <span className="text-[11px] text-muted-foreground">Pruebe:</span>
        {quickQueries[source].map((term) => (
          <button
            key={term}
            type="button"
            onClick={() => onChange({ q: term })}
            className="rounded-full border border-border/80 bg-background/60 px-2.5 py-1 text-[11px] text-foreground/80 transition-colors hover:border-primary/30 hover:bg-primary/5 hover:text-primary"
          >
            {term}
          </button>
        ))}
        <Badge variant="outline" className="ml-auto hidden font-normal text-muted-foreground md:flex">
          Ignora tildes y mayúsculas
        </Badge>
      </div>
    </div>
  );
}
