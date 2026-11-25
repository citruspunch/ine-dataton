"use client";

import { Flag, Search, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { CountFacet, SourceGroup } from "@/lib/types";

const sourceOptions: Array<{ value: SourceGroup; label: string }> = [
  { value: "DPIR", label: "DPIR — Precios de referencia" },
  { value: "IPMC", label: "IPMC — Materiales de construcción" },
  { value: "ICC", label: "ICC — Costo de construcción" },
  { value: "BASKETS", label: "CBAU / CBAR — Canastas básicas" },
];

const quickQueries: Record<SourceGroup, string[]> = {
  DPIR: ["computadora", "papel bond", "guantes", "arroz"],
  IPMC: ["cemento", "acero", "madera", "tubería"],
  ICC: ["materiales", "mano de obra", "cimentación"],
  BASKETS: ["arroz", "tortillas", "pollo", "frijol"],
};

export function Filters({
  source,
  q,
  from,
  to,
  metric,
  unit,
  includeAlerts,
  alertCount,
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
  includeAlerts: boolean;
  alertCount: number;
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
    alerts?: boolean;
  }) => void;
  onClear: () => void;
}) {
  const hasFilters = Boolean(q || from || to || unit || includeAlerts);

  return (
    <Card className="border-border/70 bg-card/90 p-4 shadow-sm sm:p-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
        <div className="min-w-0 flex-1">
          <Label htmlFor="search" className="sr-only">
            Buscar producto, material o categoría
          </Label>
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <Input
              id="search"
              list="item-suggestions"
              value={q}
              onChange={(event) => onChange({ q: event.target.value })}
              placeholder="Buscar producto, material o categoría…"
              className="h-12 rounded-lg border-border bg-background pl-10 pr-10 text-[15px] shadow-none"
              autoComplete="off"
            />
            {q ? (
              <button
                type="button"
                onClick={() => onChange({ q: "" })}
                aria-label="Limpiar búsqueda"
                className="absolute right-3 top-1/2 grid size-6 -translate-y-1/2 place-items-center rounded text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <X className="size-4" aria-hidden />
              </button>
            ) : null}
          </div>
          <datalist id="item-suggestions">
            {suggestions.map((item) => (
              <option key={item} value={item} />
            ))}
          </datalist>
        </div>

        <div className="w-full lg:w-[260px]">
          <Label className="mb-1.5 block text-xs font-medium text-muted-foreground">
            Fuente
          </Label>
          <Select value={source} onValueChange={(value) => onChange({ source: value as SourceGroup })}>
            <SelectTrigger className="h-12 w-full rounded-lg border-border bg-background text-[14px]">
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

      </div>

      <div className="mt-3 flex flex-wrap items-end gap-3">
        <div className="w-[148px]">
          <Label htmlFor="from" className="mb-1.5 block text-xs font-medium text-muted-foreground">
            Desde
          </Label>
          <Input
            id="from"
            type="month"
            lang="es-GT"
            value={from}
            onChange={(event) => onChange({ from: event.target.value })}
            className="h-10 rounded-lg border-border bg-background text-sm"
          />
        </div>
        <div className="w-[148px]">
          <Label htmlFor="to" className="mb-1.5 block text-xs font-medium text-muted-foreground">
            Hasta
          </Label>
          <Input
            id="to"
            type="month"
            lang="es-GT"
            value={to}
            onChange={(event) => onChange({ to: event.target.value })}
            className="h-10 rounded-lg border-border bg-background text-sm"
          />
        </div>

        {metrics.length > 1 ? (
          <div className="w-[220px]">
            <Label className="mb-1.5 block text-xs font-medium text-muted-foreground">
              Métrica
            </Label>
            <Select value={metric} onValueChange={(value) => onChange({ metric: value })}>
              <SelectTrigger className="h-10 w-full rounded-lg border-border bg-background text-sm">
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
        ) : null}

        {units.length > 1 ? (
          <div className="w-[220px]">
            <Label className="mb-1.5 block text-xs font-medium text-muted-foreground">
              Presentación
            </Label>
            <Select
              value={unit || "__all__"}
              onValueChange={(value) => onChange({ unit: value === "__all__" ? "" : value })}
            >
              <SelectTrigger className="h-10 w-full rounded-lg border-border bg-background text-sm">
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
          </div>
        ) : null}

        <Button
          type="button"
          size="sm"
          variant={includeAlerts ? "secondary" : "outline"}
          onClick={() => onChange({ alerts: !includeAlerts })}
          className="h-10 gap-2 rounded-lg px-3 text-sm"
        >
          <Flag className="size-4" aria-hidden />
          {includeAlerts ? "Ocultar alertas" : "Mostrar alertas"}
          {alertCount > 0 ? (
            <Badge variant="secondary" className="h-5 min-w-5 px-1.5 text-[11px] font-medium">
              {alertCount}
            </Badge>
          ) : null}
        </Button>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span>Ejemplos:</span>
        {quickQueries[source].map((term) => (
          <button
            key={term}
            type="button"
            onClick={() => onChange({ q: term })}
            className="rounded-md border border-border/70 bg-background px-2.5 py-1 text-xs text-foreground/80 transition-colors hover:border-primary/30 hover:text-primary"
          >
            {term}
          </button>
        ))}
        {hasFilters ? (
          <button
            type="button"
            onClick={onClear}
            className="ml-auto text-xs text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
          >
            Limpiar filtros
          </button>
        ) : null}
      </div>
    </Card>
  );
}
