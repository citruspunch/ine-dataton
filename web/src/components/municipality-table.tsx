"use client";

import * as React from "react";
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronRight, X } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PressureBadge, SuppressionBadge } from "@/components/pressure-badge";
import {
  formatCurrency,
  formatIndicatorValue,
  formatInteger,
  formatPercent,
  formatRatio,
  normalizeSearch,
} from "@/lib/format";
import type {
  IndicatorFormat,
  IndicatorsPayload,
  Municipality,
  PressureClass,
} from "@/lib/types";
import { cn } from "@/lib/utils";

type SortDirection = "asc" | "desc";

type Column = {
  key: string;
  label: string;
  format?: IndicatorFormat;
  align?: "left" | "right";
  sortable?: boolean;
  className?: string;
};

const COLUMNS: Column[] = [
  { key: "municipio_nombre", label: "Municipio", sortable: true, className: "min-w-[220px]" },
  { key: "poblacion_2025", label: "Población 2025", format: "integer", align: "right" },
  {
    key: "crecimiento_poblacional_pct",
    label: "Crecimiento 2025–35",
    format: "percent",
    align: "right",
  },
  {
    key: "nacimientos_por_escuela_2025",
    label: "Nac. / escuela",
    format: "ratio",
    align: "right",
  },
  {
    key: "asignacion_por_habitante_2026_gtq",
    label: "Asignación Q/hab.",
    format: "currency",
    align: "right",
  },
  { key: "pressure", label: "Presión", align: "left" },
  { key: "open", label: "", align: "right", sortable: false },
];

const PAGE_SIZE = 12;

function accessor(municipality: Municipality, key: string, indicatorKey: string): number | string | null {
  if (key === "pressure") {
    return municipality.presion[indicatorKey]?.rank_nacional ?? null;
  }
  const value = municipality[key as keyof Municipality];
  if (typeof value === "number" || typeof value === "string") return value;
  return null;
}

function compareValues(a: number | string | null, b: number | string | null): number {
  if (a === null && b === null) return 0;
  if (a === null) return 1;
  if (b === null) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b), "es", { sensitivity: "base" });
}

function displayValue(
  municipality: Municipality,
  column: Column,
  indicatorKey: string,
): React.ReactNode {
  const field = column.key;

  if (field === "open") {
    return (
      <span className="inline-flex size-7 items-center justify-center rounded-full text-muted-foreground transition-colors group-hover:bg-muted group-hover:text-foreground">
        <ChevronRight className="size-4" />
      </span>
    );
  }

  if (field === "pressure") {
    const score = municipality.presion[indicatorKey];
    return (
      <div className="flex flex-col items-start gap-1">
        <PressureBadge value={(score?.clase ?? "sin_dato") as PressureClass} />
        {score?.rank_nacional ? (
          <span className="text-[11px] text-muted-foreground">
            Puesto #{score.rank_nacional} nacional
          </span>
        ) : null}
      </div>
    );
  }

  if (field === "municipio_nombre") {
    return (
      <div className="flex items-start gap-2">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium text-foreground">
            {municipality.municipio_nombre}
          </div>
          <div className="mt-0.5 text-xs text-muted-foreground">
            {municipality.municipio_codigo} · {municipality.departamento_nombre}
          </div>
        </div>
        {municipality.campos_suprimidos.length ? (
          <SuppressionBadge fields={municipality.campos_suprimidos} className="mt-0.5" />
        ) : null}
      </div>
    );
  }

  const value = municipality[field as keyof Municipality] as number | null;
  const suppressed = municipality.campos_suprimidos.includes(field);
  if (suppressed) {
    return (
      <span className="text-muted-foreground" title="Celda suprimida por secreto estadístico.">
        — <span className="text-[10px]">§</span>
      </span>
    );
  }
  if (value === null || value === undefined || Number.isNaN(value)) {
    return <span className="text-muted-foreground">n.d.</span>;
  }
  if (column.format === "integer") {
    return <span className="font-mono tabular-nums">{formatInteger(value)}</span>;
  }
  if (column.format === "percent") {
    return <span className="font-mono tabular-nums">{formatPercent(value)}</span>;
  }
  return (
    <span className="font-mono tabular-nums">
      {formatIndicatorValue(value, column.format ?? "ratio")}
    </span>
  );
}

export function MunicipalityTable({
  data,
  search,
  indicatorKey,
  departmentFilter,
  departmentName,
  onToggleDepartment,
  onClearSearch,
  onOpenMunicipality,
}: {
  data: IndicatorsPayload;
  search: string;
  indicatorKey: string;
  departmentFilter: string;
  departmentName: string;
  onToggleDepartment: () => void;
  onClearSearch: () => void;
  onOpenMunicipality: (municipality: Municipality) => void;
}) {
  const [sortKey, setSortKey] = React.useState("pressure");
  const [sortDirection, setSortDirection] = React.useState<SortDirection>("asc");
  const [page, setPage] = React.useState(0);

  React.useEffect(() => {
    setPage(0);
  }, [search, indicatorKey, departmentFilter, sortKey, sortDirection]);

  const filtered = React.useMemo(() => {
    const needle = normalizeSearch(search);
    return data.municipalities.filter((municipality) => {
      if (departmentFilter !== "all" && municipality.departamento_codigo !== departmentFilter) {
        return false;
      }
      if (!needle) return true;
      const haystack = normalizeSearch(
        `${municipality.municipio_codigo} ${municipality.municipio_nombre} ${municipality.departamento_nombre}`,
      );
      return haystack.includes(needle);
    });
  }, [data.municipalities, departmentFilter, search]);

  const sorted = React.useMemo(() => {
    const copy = [...filtered];
    copy.sort((a, b) => {
      const direction = sortDirection === "asc" ? 1 : -1;
      return (
        direction *
        compareValues(accessor(a, sortKey, indicatorKey), accessor(b, sortKey, indicatorKey))
      );
    });
    return copy;
  }, [filtered, indicatorKey, sortDirection, sortKey]);

  const pageCount = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const start = sorted.length === 0 ? 0 : safePage * PAGE_SIZE + 1;
  const end = Math.min((safePage + 1) * PAGE_SIZE, sorted.length);
  const pageRows = sorted.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE);

  function toggleSort(key: string) {
    if (sortKey === key) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection(key === "pressure" ? "asc" : "desc");
    }
  }

  const definition = data.indicators.find((item) => item.key === indicatorKey);
  const showingDepartment = departmentFilter !== "all";

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Tabla municipal</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {showingDepartment
              ? `${departmentName}: ${filtered.length} municipios`
              : `Los ${filtered.length} municipios`}
            {search ? ` · búsqueda “${search}”` : ""}. Haga clic en una fila para ver la ficha.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {search ? (
            <Button variant="ghost" size="sm" onClick={onClearSearch}>
              <X className="size-3.5" /> Limpiar búsqueda
            </Button>
          ) : null}
          {showingDepartment ? (
            <Button variant="outline" size="sm" onClick={onToggleDepartment}>
              Ver los 340
            </Button>
          ) : departmentName !== "Todos los departamentos" ? (
            <Button variant="outline" size="sm" onClick={onToggleDepartment}>
              Solo {departmentName}
            </Button>
          ) : null}
          <Badge variant="secondary" className="font-mono text-[11px]">
            {filtered.length} / 340
          </Badge>
        </div>
      </div>

      <div className="mt-4 flex items-center gap-2 sm:hidden">
        <span className="shrink-0 text-xs text-muted-foreground">Ordenar por</span>
        <Select
          value={sortKey}
          onValueChange={(value) => {
            setSortKey(value);
            setSortDirection(
              value === "pressure" || value === "municipio_nombre" ? "asc" : "desc",
            );
          }}
        >
          <SelectTrigger className="h-8 min-w-0 flex-1 bg-background">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="pressure">Presión</SelectItem>
            <SelectItem value="municipio_nombre">Nombre</SelectItem>
            <SelectItem value="poblacion_2025">Población</SelectItem>
            <SelectItem value="crecimiento_poblacional_pct">Crecimiento</SelectItem>
            <SelectItem value="nacimientos_por_escuela_2025">Nac. por escuela</SelectItem>
            <SelectItem value="asignacion_por_habitante_2026_gtq">Asignación Q/hab.</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="mt-4 space-y-2 sm:hidden">
        {pageRows.map((municipality) => {
          const score = municipality.presion[indicatorKey];
          return (
            <button
              key={municipality.municipio_codigo}
              type="button"
              onClick={() => onOpenMunicipality(municipality)}
              className="w-full rounded-xl border bg-card p-4 text-left transition-colors hover:bg-muted/40 focus-visible:bg-muted/40 focus-visible:outline-none"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="line-clamp-2 text-sm font-medium leading-snug">
                    {municipality.municipio_nombre}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {municipality.municipio_codigo} · {municipality.departamento_nombre}
                  </p>
                </div>
                <PressureBadge value={score?.clase ?? "sin_dato"} />
              </div>
              <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                <div>
                  <p className="text-muted-foreground">Población</p>
                  <p className="mt-0.5 font-mono font-medium">
                    {formatInteger(municipality.poblacion_2025)}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Crecimiento</p>
                  <p className="mt-0.5 font-mono font-medium">
                    {formatPercent(municipality.crecimiento_poblacional_pct)}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Nac. / escuela</p>
                  <p className="mt-0.5 font-mono font-medium">
                    {formatRatio(municipality.nacimientos_por_escuela_2025)}
                  </p>
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
                <span>
                  {formatCurrency(municipality.asignacion_por_habitante_2026_gtq)} por habitante
                </span>
                {municipality.campos_suprimidos.length ? (
                  <SuppressionBadge fields={municipality.campos_suprimidos} />
                ) : null}
              </div>
            </button>
          );
        })}
        {pageRows.length === 0 ? (
          <div className="rounded-xl border bg-card p-8 text-center">
            <p className="text-sm font-medium">No se encontraron municipios</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Pruebe con otro nombre, código o departamento.
            </p>
          </div>
        ) : null}
      </div>

      <div className="mt-4 hidden overflow-hidden rounded-xl border sm:block">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader className="bg-card">
              <TableRow>
                {COLUMNS.map((column) => {
                  const isActive = sortKey === column.key;
                  const ariaSort = isActive
                    ? sortDirection === "asc"
                      ? "ascending"
                      : "descending"
                    : "none";
                  return (
                    <TableHead
                      key={column.key}
                      aria-sort={ariaSort}
                      className={cn(
                        "h-10 whitespace-nowrap bg-card px-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground",
                        column.align === "right" && "text-right",
                        column.className,
                      )}
                    >
                      {column.sortable !== false ? (
                        <button
                          type="button"
                          onClick={() => toggleSort(column.key)}
                          className={cn(
                            "inline-flex items-center gap-1 rounded-sm text-left hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                            column.align === "right" && "justify-end",
                          )}
                        >
                          {column.label}
                          {isActive ? (
                            sortDirection === "asc" ? (
                              <ArrowUp className="size-3" />
                            ) : (
                              <ArrowDown className="size-3" />
                            )
                          ) : (
                            <ArrowUpDown className="size-3 opacity-30" />
                          )}
                        </button>
                      ) : (
                        column.label
                      )}
                    </TableHead>
                  );
                })}
              </TableRow>
            </TableHeader>
            <TableBody>
              {pageRows.map((municipality) => (
                <TableRow
                  key={municipality.municipio_codigo}
                  tabIndex={0}
                  role="button"
                  aria-label={`Ver ficha de ${municipality.municipio_nombre}`}
                  onClick={() => onOpenMunicipality(municipality)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onOpenMunicipality(municipality);
                    }
                  }}
                  className="group cursor-pointer align-middle transition-colors hover:bg-muted/50 focus-visible:bg-muted/50 focus-visible:outline-none"
                >
                  {COLUMNS.map((column) => (
                    <TableCell
                      key={column.key}
                      className={cn(
                        "px-3 py-3 text-[13px]",
                        column.align === "right" && "text-right",
                      )}
                    >
                      {displayValue(municipality, column, indicatorKey)}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
              {pageRows.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={COLUMNS.length} className="h-32 text-center">
                    <p className="text-sm font-medium">No se encontraron municipios</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Pruebe con otro nombre, código o departamento.
                    </p>
                  </TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          Mostrando {start}–{end} de {sorted.length}
          {definition ? ` · ordenado por ${definition.short_label}` : ""}
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={safePage === 0}
            onClick={() => setPage((current) => Math.max(0, current - 1))}
          >
            Anterior
          </Button>
          <span className="min-w-12 text-center text-xs text-muted-foreground">
            {safePage + 1} / {pageCount}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={safePage >= pageCount - 1}
            onClick={() => setPage((current) => Math.min(pageCount - 1, current + 1))}
          >
            Siguiente
          </Button>
        </div>
      </div>

      <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground">
        <span className="font-mono">§</span> Celda suprimida por secreto estadístico (conteo 1–4 o
        tasa derivada). <span className="font-mono">n.d.</span> = no publicado en la fuente. Las
        clases de presión son percentiles relativos; no son umbrales oficiales.
      </p>
    </div>
  );
}
