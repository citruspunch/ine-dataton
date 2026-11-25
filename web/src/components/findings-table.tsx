"use client";

import { ChevronLeft, ChevronRight, Loader2, SearchX } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import {
  flagDescription,
  flagLabel,
  formatDate,
  formatNumber,
  truncate,
} from "@/lib/format";
import type { QueryResult, RecordItem } from "@/lib/types";

const datasetLabel: Record<string, string> = {
  "dpir-2022": "DPIR 2022",
  "dpir-2023": "DPIR 2023",
  "ipmc-history": "IPMC",
  "icc-2026": "ICC 2026",
  "cbau-percapita": "CBAU per cápita",
  "cbar-percapita": "CBAR per cápita",
  "cbau-history": "CBAU productos",
  "cbar-history": "CBAR productos",
};

const flagStyles: Record<string, string> = {
  invalid_date: "border-destructive/25 bg-destructive/5 text-destructive",
  missing_date: "border-destructive/20 bg-destructive/5 text-destructive",
  duplicate: "border-border bg-muted text-muted-foreground",
  thousands_comma: "border-amber-300 bg-amber-50 text-amber-800",
  missing_nog: "border-border bg-muted text-muted-foreground",
  missing_value: "border-destructive/25 bg-destructive/5 text-destructive",
  missing_product: "border-destructive/25 bg-destructive/5 text-destructive",
};

function unitText(record: RecordItem): string {
  if (record.valueKind === "index") return record.metricUnit ?? "índice";
  if (record.valueKind === "cost") return "Q por persona al mes";
  return record.unit ?? "—";
}

function QualityCell({ record }: { record: RecordItem }) {
  if (record.flags.length === 0) {
    return <span className="text-sm text-muted-foreground">—</span>;
  }
  return (
    <div className="flex flex-wrap gap-1">
      {record.flags.map((flag) => (
        <Badge
          key={flag}
          variant="outline"
          title={flagDescription(flag)}
          className={cn("h-5 px-1.5 text-[11px] font-normal", flagStyles[flag])}
        >
          {flagLabel(flag)}
        </Badge>
      ))}
    </div>
  );
}

export function FindingsTable({
  result,
  loading,
  includeAlerts,
  onPageChange,
}: {
  result: QueryResult;
  loading: boolean;
  includeAlerts: boolean;
  onPageChange: (page: number) => void;
}) {
  const { records, total, page, pageSize, pageCount, group, quality } = result;
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);
  const hiddenAlerts = Math.max(0, quality.totalRecords - total);

  return (
    <Card className="overflow-hidden border-border/70 bg-card shadow-none">
      <CardHeader className="border-b border-border/60 pb-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2 font-heading text-xl">
              Registros
              {loading ? <Loader2 className="size-4 animate-spin text-muted-foreground" aria-label="Cargando" /> : null}
            </CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">
              {formatNumber(total)} resultados
              {includeAlerts ? " · incluye alertas" : " · solo registros válidos"}
            </p>
          </div>
          {hiddenAlerts > 0 && !includeAlerts ? (
            <span className="text-xs text-muted-foreground">
              {formatNumber(hiddenAlerts)} con alertas ocultos
            </span>
          ) : null}
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className={cn("transition-opacity", loading && "pointer-events-none opacity-50")}>
          <div className="hidden sm:block">
          <Table className="min-w-[620px] table-fixed">
            <TableHeader>
              <TableRow className="bg-muted/30 hover:bg-muted/30">
                <TableHead className={cn("pl-5 text-xs font-medium text-muted-foreground", includeAlerts ? "w-[47%]" : "w-[55%]")}>
                  Producto / material
                </TableHead>
                <TableHead className={cn("text-xs font-medium text-muted-foreground", includeAlerts ? "w-[15%]" : "w-[18%]")}>
                  Fecha
                </TableHead>
                <TableHead className={cn("text-right text-xs font-medium text-muted-foreground", includeAlerts ? "w-[15%]" : "w-[27%]")}>
                  Valor
                </TableHead>
                {includeAlerts ? (
                  <TableHead className="w-[23%] text-xs font-medium text-muted-foreground">
                    Calidad
                  </TableHead>
                ) : null}
              </TableRow>
            </TableHeader>
            <TableBody>
              {records.length === 0 ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell colSpan={includeAlerts ? 4 : 3} className="h-56 text-center">
                    <div className="mx-auto flex max-w-sm flex-col items-center gap-3">
                      <span className="grid size-10 place-items-center rounded-full bg-muted text-muted-foreground">
                        <SearchX className="size-5" aria-hidden />
                      </span>
                      <div>
                        <p className="text-base font-medium">No hay registros con estos filtros</p>
                        <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                          Pruebe un término más general o cambie de fuente. La búsqueda
                          funciona con fragmentos.
                        </p>
                      </div>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                records.map((record) => (
                  <TableRow key={record.id} className="align-top">
                    <TableCell className="whitespace-normal py-4 pl-5">
                      <div className="line-clamp-2 break-words text-[15px] font-medium leading-snug">
                        {truncate(record.item, 110)}
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        {record.category}
                        {record.context ? ` · ${record.context}` : ""}
                        <span className="text-muted-foreground/70">
                          {" "}
                          · {datasetLabel[record.dataset] ?? record.dataset}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="whitespace-normal py-4 text-sm">
                      {record.date
                        ? formatDate(record.date, group.granularity)
                        : record.dateRaw ?? "Sin fecha"}
                    </TableCell>
                    <TableCell className="whitespace-normal py-4 text-right">
                      <div className="font-mono text-[15px] font-semibold leading-none tabular">
                        {formatNumber(record.value)}
                      </div>
                      <div className="mt-1.5 text-xs leading-tight text-muted-foreground">
                        {unitText(record)}
                      </div>
                    </TableCell>
                    {includeAlerts ? (
                      <TableCell className="whitespace-normal py-4">
                        <QualityCell record={record} />
                      </TableCell>
                    ) : null}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
          </div>

          <div className="divide-y divide-border/60 sm:hidden">
            {records.length === 0 ? (
              <div className="px-5 py-12 text-center text-sm text-muted-foreground">
                No hay registros con estos filtros.
              </div>
            ) : (
              records.map((record) => (
                <div key={record.id} className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="line-clamp-2 break-words text-[15px] font-medium leading-snug">
                        {truncate(record.item, 110)}
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        {record.category} · {datasetLabel[record.dataset] ?? record.dataset}
                      </div>
                      {includeAlerts ? (
                        <div className="mt-2">
                          <QualityCell record={record} />
                        </div>
                      ) : null}
                    </div>
                    <div className="shrink-0 text-right">
                      <div className="font-mono text-[15px] font-semibold leading-none tabular">
                        {formatNumber(record.value)}
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">{unitText(record)}</div>
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">
                    {record.date
                      ? formatDate(record.date, group.granularity)
                      : record.dateRaw ?? "Sin fecha"}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border/60 px-5 py-3">
          <p className="text-xs text-muted-foreground">
            {total === 0
              ? "Sin resultados"
              : `Mostrando ${formatNumber(start)}–${formatNumber(end)} de ${formatNumber(total)}`}
          </p>
          <div className="flex items-center gap-1.5">
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={page <= 1 || loading}
              onClick={() => onPageChange(page - 1)}
              className="h-8 gap-1 px-2.5"
            >
              <ChevronLeft className="size-4" aria-hidden />
              Anterior
            </Button>
            <span className="min-w-14 text-center text-xs tabular text-muted-foreground">
              {page} / {pageCount}
            </span>
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={page >= pageCount || loading}
              onClick={() => onPageChange(page + 1)}
              className="h-8 gap-1 px-2.5"
            >
              Siguiente
              <ChevronRight className="size-4" aria-hidden />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
