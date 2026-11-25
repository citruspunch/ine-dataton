"use client";

import * as React from "react";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ListFilter,
  Search,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
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

type SortKey = "name" | "group" | "unitPrice" | "kcal" | "cost" | "kcalCost";
type SortDirection = "asc" | "desc";

type ProductsTableProps = {
  area: Area;
  month: AreaMonth;
  members: number;
  mode: Mode;
};

const COLLATOR = new Intl.Collator("es", { sensitivity: "base" });

function normalize(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function SortButton({
  label,
  sortKey,
  activeKey,
  direction,
  onClick,
  align = "left",
}: {
  label: string;
  sortKey: SortKey;
  activeKey: SortKey;
  direction: SortDirection;
  onClick: (key: SortKey) => void;
  align?: "left" | "right";
}) {
  const active = activeKey === sortKey;
  const Icon = !active ? ArrowUpDown : direction === "asc" ? ArrowUp : ArrowDown;
  return (
    <button
      type="button"
      onClick={() => onClick(sortKey)}
      className={`inline-flex w-full items-center gap-1 text-[11px] font-medium transition-colors hover:text-foreground ${
        align === "right" ? "justify-end" : "justify-start"
      } ${active ? "text-foreground" : "text-muted-foreground"}`}
      aria-label={`Ordenar por ${label}`}
    >
      {label}
      <Icon className={`size-3 ${active ? "opacity-100" : "opacity-45"}`} />
    </button>
  );
}

export function ProductsTable({ area, month, members, mode }: ProductsTableProps) {
  const data = areaData(area);
  const [query, setQuery] = React.useState("");
  const [groupFilter, setGroupFilter] = React.useState("all");
  // Sin efectos: el orden por defecto depende del modo hasta que la persona
  // elige explícitamente una columna.
  const [sortKey, setSortKey] = React.useState<SortKey | null>(null);
  const [direction, setDirection] = React.useState<SortDirection>("desc");
  const activeSortKey: SortKey =
    sortKey ?? (mode === "total" ? "cost" : "kcalCost");

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
      const matchesGroup =
        groupFilter === "all" || row.group === groupFilter;
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
      // Los productos de 0 kcal siempre al final en el orden por costo calórico.
      if (activeSortKey === "kcalCost") {
        const aValue = a.costPerThousandKcal;
        const bValue = b.costPerThousandKcal;
        if (aValue === null && bValue === null) return COLLATOR.compare(a.name, b.name);
        if (aValue === null) return 1;
        if (bValue === null) return -1;
        return (aValue - bValue) * factor;
      }
      switch (activeSortKey) {
        case "name":
          return COLLATOR.compare(a.name, b.name) * factor;
        case "group":
          return (
            (COLLATOR.compare(a.group, b.group) ||
              COLLATOR.compare(a.name, b.name)) * factor
          );
        case "unitPrice":
          return (a.unitPrice - b.unitPrice) * factor;
        case "kcal":
          return (a.kcalPerPersonDay - b.kcalPerPersonDay) * factor;
        case "cost":
          return (a.costPerPersonMonth - b.costPerPersonMonth) * factor;
        default:
          return 0;
      }
    });
  }, [filtered, activeSortKey, direction]);

  const handleSort = (key: SortKey) => {
    if (key === activeSortKey) {
      setDirection((current) => (current === "asc" ? "desc" : "asc"));
      setSortKey(key);
      return;
    }
    setSortKey(key);
    setDirection(key === "name" || key === "group" ? "asc" : "desc");
  };

  const zeroKcalCount = rows.filter((row) => row.zeroKcal).length;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle className="flex items-center gap-2 text-sm">
              <ListFilter className="size-4 text-primary" />
              Productos de la canasta
            </CardTitle>
            <CardDescription className="mt-0.5 text-[11px]">
              {rows.length} productos · {data.groups.length} grupos ·{" "}
              {month.label.toLowerCase()}
              {mode === "kcal"
                ? " · agua y sal excluidas del cálculo por 1.000 kcal"
                : ""}
            </CardDescription>
          </div>
          <Badge
            variant="outline"
            className="border-border bg-muted/50 font-mono text-[10px] text-muted-foreground"
          >
            CBA {area.toLowerCase()}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-2.5 pb-2">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative w-full sm:max-w-[280px]">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar producto o grupo"
              aria-label="Buscar producto o grupo"
              className="h-9 border-border/80 bg-card pl-8 pr-8 text-[12px]"
            />
            {query ? (
              <button
                type="button"
                onClick={() => setQuery("")}
                aria-label="Limpiar búsqueda"
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <X className="size-3.5" />
              </button>
            ) : null}
          </div>
          <div className="flex items-center gap-2">
            <Select value={groupFilter} onValueChange={setGroupFilter}>
              <SelectTrigger
                className="h-9 min-w-0 flex-1 text-[12px] sm:w-[220px]"
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
            <span className="shrink-0 font-mono text-[10.5px] text-muted-foreground">
              {sorted.length}/{rows.length}
            </span>
          </div>
        </div>

        <div className="scrollbar-thin max-h-[560px] overflow-auto rounded-lg border border-border/80">
          <Table>
            <TableCaption className="sr-only">
              Productos de la canasta básica alimentaria {area.toLowerCase()} para{" "}
              {month.label}, ordenados según la columna seleccionada.
            </TableCaption>
            <TableHeader className="sticky top-0 z-10 bg-card/95 backdrop-blur">
              <TableRow className="hover:bg-transparent">
                <TableHead className="h-9 min-w-[180px]">
                  <SortButton
                    label="Producto"
                    sortKey="name"
                    activeKey={activeSortKey}
                    direction={direction}
                    onClick={handleSort}
                  />
                </TableHead>
                <TableHead className="hidden h-9 md:table-cell">
                  <SortButton
                    label="Grupo"
                    sortKey="group"
                    activeKey={activeSortKey}
                    direction={direction}
                    onClick={handleSort}
                  />
                </TableHead>
                <TableHead className="hidden h-9 text-right sm:table-cell">
                  <SortButton
                    label="Precio unidad"
                    sortKey="unitPrice"
                    activeKey={activeSortKey}
                    direction={direction}
                    onClick={handleSort}
                    align="right"
                  />
                </TableHead>
                <TableHead className="hidden h-9 text-right lg:table-cell">
                  <SortButton
                    label="kcal/día"
                    sortKey="kcal"
                    activeKey={activeSortKey}
                    direction={direction}
                    onClick={handleSort}
                    align="right"
                  />
                </TableHead>
                <TableHead className="h-9 text-right">
                  <SortButton
                    label="Costo hogar/mes"
                    sortKey="cost"
                    activeKey={activeSortKey}
                    direction={direction}
                    onClick={handleSort}
                    align="right"
                  />
                </TableHead>
                <TableHead className="h-9 text-right">
                  <SortButton
                    label="Q/1.000 kcal"
                    sortKey="kcalCost"
                    activeKey={activeSortKey}
                    direction={direction}
                    onClick={handleSort}
                    align="right"
                  />
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sorted.map((row) => (
                <TableRow
                  key={row.name}
                  className={
                    row.zeroKcal
                      ? "text-muted-foreground hover:bg-muted/40"
                      : "hover:bg-muted/40"
                  }
                >
                  <TableCell className="py-1.5">
                    <div className="flex items-center gap-1.5">
                      <span
                        className="line-clamp-2 max-w-[360px] text-[12px] font-medium leading-snug sm:line-clamp-1"
                        title={row.name}
                      >
                        {row.name}
                      </span>
                      {row.zeroKcal ? (
                        <Badge
                          variant="outline"
                          className="border-amber-300/70 bg-amber-50 px-1.5 py-0 text-[9px] font-medium text-amber-800"
                        >
                          0 kcal
                        </Badge>
                      ) : null}
                    </div>
                    <p className="mt-0.5 text-[10px] text-muted-foreground md:hidden">
                      {row.group} · {formatUnitQuantity(row.baseQuantity, row.baseUnit)}
                    </p>
                  </TableCell>
                  <TableCell className="hidden py-1.5 md:table-cell">
                    <span className="text-[11px] text-muted-foreground">
                      {row.group}
                    </span>
                  </TableCell>
                  <TableCell className="hidden py-1.5 text-right sm:table-cell">
                    <span className="font-mono text-[11.5px] tabular-nums">
                      {formatQuetzales(row.unitPrice, 2)}
                    </span>
                    <span className="ml-1 whitespace-nowrap text-[10px] text-muted-foreground">
                      / {formatUnitQuantity(row.baseQuantity, row.baseUnit)}
                    </span>
                  </TableCell>
                  <TableCell className="hidden py-1.5 text-right lg:table-cell">
                    <span className="font-mono text-[11.5px] tabular-nums">
                      {formatNumber(row.kcalPerPersonDay, 1)}
                    </span>
                  </TableCell>
                  <TableCell className="py-1.5 text-right">
                    <span className="font-mono text-[11.5px] tabular-nums">
                      {formatQuetzales(row.costPerPersonMonth * members, 2)}
                    </span>
                  </TableCell>
                  <TableCell className="py-1.5 text-right">
                    {row.costPerThousandKcal === null ? (
                      <span
                        className="inline-flex items-center rounded-full bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
                        title="Producto sin calorías: no se calcula costo por 1.000 kcal"
                      >
                        no aplica
                      </span>
                    ) : (
                      <span
                        className={`font-mono text-[11.5px] tabular-nums ${
                          mode === "kcal"
                            ? "font-semibold text-foreground"
                            : "text-muted-foreground"
                        }`}
                      >
                        {formatQuetzales(row.costPerThousandKcal, 2)}
                      </span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {sorted.length === 0 ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell colSpan={6} className="py-8 text-center">
                    <p className="text-[12px] text-muted-foreground">
                      No hay productos que coincidan con la búsqueda.
                    </p>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-2 text-xs"
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
      </CardContent>

      <CardFooter className="justify-between gap-3 py-2.5 text-[10px] leading-snug text-muted-foreground">
        <span>
          Precio por unidad base del INE (no por kg ni comparable entre unidades
          distintas). kcal y Q/1.000 kcal por persona/día. El costo del hogar
          incluye todos los productos; la suma puede diferir del total publicado
          por redondeo.
        </span>
        <span className="shrink-0 font-mono">
          {zeroKcalCount} sin kcal
        </span>
      </CardFooter>
    </Card>
  );
}
