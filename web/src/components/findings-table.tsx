"use client";

import { AlertTriangle, Check, ChevronLeft, ChevronRight, Loader2, SearchX } from "lucide-react";

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
  "dpir-2022": "DPIR · archivo 2022",
  "dpir-2023": "DPIR · archivo 2023",
  "ipmc-history": "IPMC · histórico",
  "icc-2026": "ICC · 2026",
  "cbau-percapita": "CBAU · per cápita",
  "cbar-percapita": "CBAR · per cápita",
  "cbau-history": "CBAU · productos",
  "cbar-history": "CBAR · productos",
};

const statusBadge: Record<string, string> = {
  frozen: "border-amber-300/60 bg-amber-50 text-amber-800",
  current: "border-emerald-300/60 bg-emerald-50 text-emerald-800",
  limited: "border-sky-300/60 bg-sky-50 text-sky-800",
};

const flagBadge: Record<string, string> = {
  invalid_date: "border-destructive/30 bg-destructive/5 text-destructive",
  missing_date: "border-destructive/20 bg-destructive/5 text-destructive",
  duplicate: "border-border bg-muted text-foreground/70",
  thousands_comma: "border-amber-300/60 bg-amber-50 text-amber-800",
  missing_nog: "border-border bg-muted text-foreground/70",
  missing_value: "border-destructive/30 bg-destructive/5 text-destructive",
  missing_product: "border-destructive/30 bg-destructive/5 text-destructive",
};

function valueUnit(record: RecordItem): string {
  if (record.valueKind === "index") return "puntos de índice";
  if (record.valueKind === "cost") return "Q por persona";
  return "Q";
}

function displayUnit(record: RecordItem): string {
  if (record.valueKind === "index") return record.metricUnit ?? "Índice";
  if (record.valueKind === "cost") return "Q por persona al mes";
  return record.unit ?? "—";
}

function SourceCell({ record }: { record: RecordItem }) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-1.5">
        <span className="text-xs font-semibold">{record.source}</span>
        <Badge
          variant="outline"
          className={cn("h-4 px-1 text-[8px] font-semibold uppercase tracking-wide", statusBadge[record.status])}
        >
          {record.status === "frozen" ? "Congelado" : record.status === "limited" ? "Parcial" : "Vigente"}
        </Badge>
      </div>
      <span className="text-[10px] leading-tight text-muted-foreground">
        {datasetLabel[record.dataset] ?? record.dataset}
      </span>
    </div>
  );
}

function QualityCell({ record }: { record: RecordItem }) {
  if (record.flags.length === 0) {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground">
        <Check className="size-3 text-success" aria-hidden />
        Sin alertas
      </span>
    );
  }
  return (
    <div className="flex flex-wrap gap-1">
      {record.flags.map((flag) => (
        <Badge
          key={flag}
          variant="outline"
          title={flagDescription(flag)}
          className={cn("h-5 px-1.5 text-[9px] font-medium", flagBadge[flag])}
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
  onPageChange,
}: {
  result: QueryResult;
  loading: boolean;
  onPageChange: (page: number) => void;
}) {
  const { records, total, page, pageSize, pageCount, group, selectedMetric, selectedUnit } = result;
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  return (
    <Card className="overflow-hidden border-border/80 bg-card/85">
      <CardHeader className="gap-2 border-b border-border/70 pb-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              Hallazgos
            </p>
            <CardTitle className="mt-1 flex items-center gap-2 font-heading text-xl">
              Registros que coinciden
              {loading ? <Loader2 className="size-4 animate-spin text-muted-foreground" aria-label="Cargando" /> : null}
            </CardTitle>
            <p className="mt-1 text-xs text-muted-foreground">
              {selectedMetric ?? group.label}
              {selectedUnit ? ` · ${selectedUnit}` : ""} · {formatNumber(total)} registros
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="font-normal text-muted-foreground">
              {group.shortLabel}
            </Badge>
            <Badge variant="outline" className={cn("font-medium", statusBadge[group.status])}>
              {group.statusLabel}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className={cn("transition-opacity", loading && "pointer-events-none opacity-55")}>
          <Table className="min-w-[760px] table-fixed">
            <TableHeader>
              <TableRow className="bg-muted/40 hover:bg-muted/40">
                <TableHead className="w-[38%] pl-4 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                  Producto / material
                </TableHead>
                <TableHead className="w-[15%] text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                  Fuente
                </TableHead>
                <TableHead className="w-[12%] text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                  Fecha
                </TableHead>
                <TableHead className="w-[13%] text-right text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                  Valor
                </TableHead>
                <TableHead className="w-[22%] text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">
                  Calidad
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {records.length === 0 ? (
                <TableRow className="hover:bg-transparent">
                  <TableCell colSpan={5} className="h-56 text-center">
                    <div className="mx-auto flex max-w-md flex-col items-center gap-3">
                      <span className="grid size-11 place-items-center rounded-full bg-muted text-muted-foreground">
                        <SearchX className="size-5" aria-hidden />
                      </span>
                      <div>
                        <p className="font-medium">No hay registros con estos filtros.</p>
                        <p className="mt-1 text-sm text-muted-foreground">
                          Pruebe un término más general, quite el filtro de presentación o cambie
                          la fuente. La búsqueda funciona con fragmentos: “cemento”, “varilla”,
                          “arroz”.
                        </p>
                      </div>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                records.map((record) => {
                  const invalidDate = record.dateStatus !== "valid";
                  return (
                    <TableRow key={record.id} className="align-top">
                      <TableCell className="whitespace-normal py-3 pl-4">
                        <div className="line-clamp-2 break-words font-medium leading-snug">
                          {truncate(record.item, 120)}
                        </div>
                        <div className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-muted-foreground">
                          <span>{record.category}</span>
                          {record.context ? <span>· {record.context}</span> : null}
                          {record.level ? <span>· {record.level}</span> : null}
                          {record.region ? <span>· {record.region}</span> : null}
                          {record.nog ? <span>· NOG {record.nog}</span> : null}
                        </div>
                        {record.description ? (
                          <div className="mt-1 line-clamp-1 text-[10px] leading-relaxed text-muted-foreground/80">
                            {record.description}
                          </div>
                        ) : null}
                      </TableCell>
                      <TableCell className="py-3">
                        <SourceCell record={record} />
                      </TableCell>
                      <TableCell className="py-3">
                        <div className={cn("text-xs tabular", invalidDate && "text-destructive")}>
                          {record.date
                            ? formatDate(record.date, group.granularity)
                            : record.dateRaw ?? "Sin fecha"}
                        </div>
                        {invalidDate && record.dateRaw ? (
                          <div className="mt-0.5 text-[9px] text-destructive/80">
                            original: {record.dateRaw}
                          </div>
                        ) : null}
                      </TableCell>
                      <TableCell className="py-3 text-right">
                        <div className="font-mono text-sm font-semibold tabular">
                          {formatNumber(record.value)}
                        </div>
                        <div className="mt-0.5 text-[9px] leading-tight text-muted-foreground">
                          {valueUnit(record)}
                        </div>
                        <div className="mt-0.5 text-[9px] leading-tight text-muted-foreground/70">
                          {displayUnit(record)}
                        </div>
                      </TableCell>
                      <TableCell className="whitespace-normal py-3">
                        <QualityCell record={record} />
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border/70 px-4 py-3">
          <p className="text-[11px] text-muted-foreground">
            {total === 0 ? "Sin resultados" : `Mostrando ${formatNumber(start)}–${formatNumber(end)} de ${formatNumber(total)}`}
            {result.quality.excludedFromStats > 0 ? (
              <span className="ml-2 inline-flex items-center gap-1 text-amber-700">
                <AlertTriangle className="size-3" aria-hidden />
                {formatNumber(result.quality.excludedFromStats)} fuera de resúmenes
              </span>
            ) : null}
          </p>
          <div className="flex items-center gap-1.5">
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={page <= 1 || loading}
              onClick={() => onPageChange(page - 1)}
              className="h-8 gap-1"
            >
              <ChevronLeft className="size-3.5" aria-hidden />
              Anterior
            </Button>
            <span className="min-w-16 text-center text-[11px] tabular text-muted-foreground">
              {page} / {pageCount}
            </span>
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={page >= pageCount || loading}
              onClick={() => onPageChange(page + 1)}
              className="h-8 gap-1"
            >
              Siguiente
              <ChevronRight className="size-3.5" aria-hidden />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
