"use client";

import * as React from "react";
import { ArrowUpDown, ChevronDown, ChevronUp, Search, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { areaData } from "@/lib/data";
import {
  formatNumber,
  formatQuetzales,
  formatUnitQuantity,
} from "@/lib/format";
import type { Area, AreaMonth, Mode, ProductRow } from "@/lib/types";

type SortKey = "name" | "price" | "cost" | "kcalCost";
type SortDirection = "asc" | "desc";

type ProductsTableProps = {
  area: Area;
  month: AreaMonth;
  members: number;
  mode: Mode;
};

const COLLATOR = new Intl.Collator("es", { sensitivity: "base" });
const INITIAL_ROWS = 6;

function normalize(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function SortHeader({
  label,
  shortLabel,
  column,
  active,
  direction,
  onSort,
  align = "left",
}: {
  label: string;
  shortLabel?: string;
  column: SortKey;
  active: SortKey;
  direction: SortDirection;
  onSort: (column: SortKey) => void;
  align?: "left" | "right";
}) {
  const isActive = active === column;
  const Icon = !isActive ? ArrowUpDown : direction === "asc" ? ChevronUp : ChevronDown;

  return (
    <button
      type="button"
      onClick={() => onSort(column)}
      aria-label={`Ordenar por ${label}`}
      className={`inline-flex w-full items-center gap-1 text-[12.5px] font-medium transition-colors hover:text-foreground ${
        align === "right" ? "justify-end" : "justify-start"
      } ${isActive ? "text-foreground" : "text-muted-foreground"}`}
    >
      {shortLabel ? (
        <>
          <span className="sm:hidden">{shortLabel}</span>
          <span className="hidden sm:inline">{label}</span>
        </>
      ) : (
        label
      )}
      <Icon className={`size-3 shrink-0 ${isActive ? "opacity-100" : "opacity-35"}`} />
    </button>
  );
}

export function ProductsTable({ area, month, members, mode }: ProductsTableProps) {
  const data = areaData(area);
  const [query, setQuery] = React.useState("");
  const [groupFilter, setGroupFilter] = React.useState("all");
  const [sortKey, setSortKey] = React.useState<SortKey | null>(null);
  const [direction, setDirection] = React.useState<SortDirection>("desc");
  const [expanded, setExpanded] = React.useState(false);

  const activeSort: SortKey = sortKey ?? (mode === "total" ? "cost" : "kcalCost");

  const rows: ProductRow[] = React.useMemo(
    () =>
      data.products.map((product, index) => {
        const values = month.productValues[index] ?? [0, 0, 0, null];
        const [unitPrice, kcal, costDay, cost1000] = values;
        return {
          ...product,
          unitPrice,
          kcalPerPersonDay: kcal,
          costPerPersonDay: costDay,
          costPerPersonMonth: costDay * 30,
          costPerThousandKcal: cost1000,
        };
      }),
    [data.products, month.productValues],
  );

  const filtered = React.useMemo(() => {
    const needle = normalize(query.trim());
    return rows.filter((row) => {
      const matchesGroup = groupFilter === "all" || row.group === groupFilter;
      const matchesQuery =
        needle.length === 0 ||
        normalize(row.name).includes(needle) ||
        normalize(row.group).includes(needle);
      return matchesGroup && matchesQuery;
    });
  }, [rows, query, groupFilter]);

  const sorted = React.useMemo(() => {
    const factor = direction === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      if (activeSort === "kcalCost") {
        const aValue = a.costPerThousandKcal;
        const bValue = b.costPerThousandKcal;
        if (aValue === null && bValue === null) return COLLATOR.compare(a.name, b.name);
        if (aValue === null) return 1;
        if (bValue === null) return -1;
        return (aValue - bValue) * factor;
      }
      switch (activeSort) {
        case "name":
          return COLLATOR.compare(a.name, b.name) * factor;
        case "price":
          return (a.unitPrice - b.unitPrice) * factor;
        case "cost":
          return (a.costPerPersonMonth - b.costPerPersonMonth) * factor;
        default:
          return 0;
      }
    });
  }, [filtered, activeSort, direction]);

  const isFiltering = query.trim().length > 0 || groupFilter !== "all";
  const limit = expanded || isFiltering ? sorted.length : INITIAL_ROWS;
  const visible = sorted.slice(0, limit);
  const canExpand = sorted.length > INITIAL_ROWS && !isFiltering;

  const handleSort = (column: SortKey) => {
    if (column === activeSort) {
      setDirection((current) => (current === "asc" ? "desc" : "asc"));
      setSortKey(column);
      return;
    }
    setSortKey(column);
    setDirection(column === "name" ? "asc" : "desc");
  };

  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle className="text-[15px]">Productos de la canasta</CardTitle>
        <CardDescription className="text-[12.5px]">
          {rows.length} productos · {month.label.toLowerCase()} · precios por
          unidad base
        </CardDescription>
      </CardHeader>

      <CardContent className="pt-3">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="relative w-full">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar producto"
              aria-label="Buscar producto"
              className="h-10 border-border/80 bg-card pl-9 pr-9 text-[13.5px]"
            />
            {query ? (
              <button
                type="button"
                onClick={() => setQuery("")}
                aria-label="Limpiar búsqueda"
                className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <X className="size-4" />
              </button>
            ) : null}
          </div>
          <Select value={groupFilter} onValueChange={setGroupFilter}>
            <SelectTrigger
              className="h-10 w-full text-[13.5px] sm:w-[230px]"
              aria-label="Filtrar por grupo de alimentos"
            >
              <SelectValue placeholder="Grupo" />
            </SelectTrigger>
            <SelectContent className="max-h-[320px]">
              <SelectItem value="all">Todos los grupos</SelectItem>
              {data.groups.map((group) => (
                <SelectItem key={group} value={group}>
                  {group}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div
          className={`mt-3 overflow-auto rounded-lg border border-border/70 ${
            expanded ? "scrollbar-thin max-h-[560px]" : ""
          }`}
        >
          <Table className="table-fixed">
            <TableCaption className="sr-only">
              Productos de la canasta básica alimentaria {area.toLowerCase()} para{" "}
              {month.label}.
            </TableCaption>
            <TableHeader
              className={expanded ? "sticky top-0 z-10 bg-card/95 backdrop-blur" : ""}
            >
              <TableRow className="hover:bg-transparent">
                <TableHead className="h-10 pl-3">
                  <SortHeader
                    label="Producto"
                    column="name"
                    active={activeSort}
                    direction={direction}
                    onSort={handleSort}
                  />
                </TableHead>
                <TableHead className="hidden h-10 w-[104px] text-right sm:table-cell">
                  <SortHeader
                    label="Precio"
                    column="price"
                    active={activeSort}
                    direction={direction}
                    onSort={handleSort}
                    align="right"
                  />
                </TableHead>
                <TableHead
                  className={`h-10 text-right sm:w-[104px] ${
                    mode === "kcal" ? "hidden sm:table-cell" : "w-[92px]"
                  }`}
                >
                  <SortHeader
                    label="Costo hogar"
                    shortLabel="Costo"
                    column="cost"
                    active={activeSort}
                    direction={direction}
                    onSort={handleSort}
                    align="right"
                  />
                </TableHead>
                <TableHead
                  className={`h-10 pr-3 text-right sm:w-[108px] ${
                    mode === "total" ? "hidden sm:table-cell" : "w-[92px]"
                  }`}
                >
                  <SortHeader
                    label="Q/1.000 kcal"
                    shortLabel="Q/1k"
                    column="kcalCost"
                    active={activeSort}
                    direction={direction}
                    onSort={handleSort}
                    align="right"
                  />
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {visible.map((row) => (
                <TableRow
                  key={row.name}
                  className={row.zeroKcal ? "text-muted-foreground" : ""}
                >
                  <TableCell className="min-w-0 whitespace-normal py-3 pl-3">
                    <div className="flex min-w-0 items-center gap-2">
                      <span
                        className="line-clamp-2 min-w-0 break-words text-[13px] font-medium leading-snug text-foreground sm:text-[13.5px]"
                        title={row.name}
                      >
                        {row.name}
                      </span>
                      {row.zeroKcal ? (
                        <Badge
                          variant="outline"
                          className="border-border bg-muted/60 px-1.5 py-0 text-[11px] font-medium text-muted-foreground"
                        >
                          0 kcal
                        </Badge>
                      ) : null}
                    </div>
                    <p className="mt-0.5 line-clamp-2 break-words text-[12px] leading-snug text-muted-foreground">
                      <span className="hidden sm:inline">{row.group} · </span>
                      <span className="sm:hidden">
                        {formatQuetzales(row.unitPrice)}/
                        {formatUnitQuantity(row.baseQuantity, row.baseUnit)} ·{" "}
                      </span>
                      {row.zeroKcal ? (
                        "sin calorías"
                      ) : (
                        <>
                          {formatNumber(
                            row.kcalPerPersonDay,
                            row.kcalPerPersonDay < 10 ? 1 : 0,
                          )}{" "}
                          kcal
                        </>
                      )}
                    </p>
                  </TableCell>
                  <TableCell className="hidden py-3 text-right sm:table-cell">
                    <span className="font-mono text-[13.5px] tabular-nums">
                      {formatQuetzales(row.unitPrice)}
                    </span>
                    <p className="text-[11.5px] text-muted-foreground">
                      {formatUnitQuantity(row.baseQuantity, row.baseUnit)}
                    </p>
                  </TableCell>
                  <TableCell
                    className={`whitespace-nowrap px-2 py-3 text-right sm:px-3 ${
                      mode === "kcal" ? "hidden sm:table-cell" : ""
                    }`}
                  >
                    <span className="block font-mono text-[12.5px] tabular-nums sm:text-[13.5px]">
                      {formatQuetzales(row.costPerPersonMonth * members)}
                    </span>
                    {row.zeroKcal ? null : (
                      <span className="mt-0.5 block text-[11.5px] text-muted-foreground sm:hidden">
                        {formatQuetzales(row.costPerThousandKcal ?? 0)}/1k
                      </span>
                    )}
                  </TableCell>
                  <TableCell
                    className={`whitespace-nowrap py-3 pr-3 text-right ${
                      mode === "total" ? "hidden sm:table-cell" : ""
                    }`}
                  >
                    {row.costPerThousandKcal === null ? (
                      <span
                        className="block text-[12.5px] text-muted-foreground"
                        title="Producto sin calorías: no tiene costo por 1.000 kcal"
                      >
                        —
                      </span>
                    ) : (
                      <span
                        className={`block font-mono text-[12.5px] tabular-nums sm:text-[13.5px] ${
                          mode === "kcal"
                            ? "font-semibold text-foreground"
                            : "text-muted-foreground"
                        }`}
                      >
                        {formatQuetzales(row.costPerThousandKcal)}
                      </span>
                    )}
                    <span className="mt-0.5 block text-[11.5px] text-muted-foreground sm:hidden">
                      {formatQuetzales(row.costPerPersonMonth * members)}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
              {visible.length === 0 ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell colSpan={4} className="py-10 text-center">
                    <p className="text-[13.5px] text-muted-foreground">
                      No hay productos que coincidan con la búsqueda.
                    </p>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-1 text-[13px]"
                      onClick={() => {
                        setQuery("");
                        setGroupFilter("all");
                      }}
                    >
                      Limpiar filtros
                    </Button>
                  </TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </div>

        {canExpand ? (
          <div className="mt-3 flex justify-center">
            <button
              type="button"
              onClick={() => setExpanded((current) => !current)}
              className="inline-flex items-center gap-1 text-[13px] font-medium text-primary transition-colors hover:text-primary/80"
            >
              {expanded
                ? "Ver menos productos"
                : `Ver los ${sorted.length} productos`}
              {expanded ? (
                <ChevronUp className="size-3.5" />
              ) : (
                <ChevronDown className="size-3.5" />
              )}
            </button>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
