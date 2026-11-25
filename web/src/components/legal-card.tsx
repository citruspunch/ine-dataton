"use client";

import { useMemo, useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { fmt } from "@/lib/format";
import type { DinesePayload, ViewId } from "@/lib/types";

interface LegalCardProps {
  view: ViewId;
  labels: string[];
  shortLabels: Record<string, string>;
  current: DinesePayload;
  previous: DinesePayload | null;
  categories: { current: number; previous?: number };
}

export function LegalCard({
  view,
  labels,
  shortLabels,
  current,
  previous,
  categories,
}: LegalCardProps) {
  const [open, setOpen] = useState(false);
  const isSeries = view === "series";

  const rows = useMemo(
    () =>
      labels
        .map((label) => ({
          label,
          short: shortLabels[label] ?? label,
          current: current.legal[label] ?? 0,
          prior: previous?.legal[label] ?? 0,
        }))
        .sort((a, b) => {
          const aValue = isSeries ? a.current + a.prior : a.current;
          const bValue = isSeries ? b.current + b.prior : b.current;
          return bValue - aValue || a.label.localeCompare(b.label, "es");
        }),
    [labels, shortLabels, current, previous, isSeries],
  );

  const activeRows = rows.filter((row) => row.current > 0 || row.prior > 0);
  const omitted = rows.length - activeRows.length;
  const top = activeRows.slice(0, 6);
  const rest = activeRows.slice(6);
  const restTotal = rest.reduce((sum, row) => sum + row.current, 0);
  const max = Math.max(...top.map((row) => row.current), restTotal, 1);
  const topTwo = top.slice(0, 2).reduce((sum, row) => sum + row.current, 0);
  const topTwoShare = current.total ? (topTwo / current.total) * 100 : 0;

  return (
    <>
      <Card className="shadow-sm">
        <CardContent className="flex h-full flex-col gap-4">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h2 className="text-base font-semibold tracking-tight">
                Personería jurídica
              </h2>
              <p className="mt-0.5 text-[13px] text-muted-foreground">
                Tipo registrado en DINESE · {current.year ?? 2024}
              </p>
            </div>
            <Badge
              variant="outline"
              className="h-6 rounded-full px-2.5 text-[11px] font-medium"
            >
              {isSeries
                ? `${categories.previous} / ${categories.current}`
                : `${categories.current} categorías`}
            </Badge>
          </div>

          <div className="space-y-3">
            {top.map((row) => (
              <div key={row.label} title={row.label}>
                <div className="flex items-baseline justify-between gap-2">
                  <span className="truncate text-[12.5px]">{row.short}</span>
                  <span className="shrink-0 font-mono text-[12px] tabular-nums">
                    {fmt(row.current)}
                  </span>
                </div>
                <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-chart-2"
                    style={{ width: `${(row.current / max) * 100}%` }}
                  />
                </div>
              </div>
            ))}
            {rest.length ? (
              <div className="flex items-center justify-between gap-2 border-t border-dashed pt-2 text-[12px] text-muted-foreground">
                <span>Otras {rest.length} categorías</span>
                <span className="font-mono">{fmt(restTotal)}</span>
              </div>
            ) : null}
          </div>

          <div className="mt-auto space-y-3">
            <p className="rounded-lg bg-secondary/40 px-3 py-2 text-[11.5px] leading-relaxed text-muted-foreground">
              Las dos categorías principales concentran{" "}
              <span className="font-medium text-foreground">
                {topTwoShare.toFixed(1)} %
              </span>{" "}
              del total.
            </p>
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-dashed pt-3">
            <p className="text-[11.5px] text-muted-foreground">
              Etiquetas oficiales, sin homologar entre años.
            </p>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 gap-1 px-2 text-[12px] text-primary"
              onClick={() => setOpen(true)}
            >
              Ver todas <ArrowUpRight className="size-3.5" />
            </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-h-[82vh] overflow-y-auto sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Personería jurídica</DialogTitle>
            <DialogDescription>
              Todas las categorías registradas en {current.year ?? 2024}
              {isSeries ? ", con la referencia de 2021." : "."} No se fuerza
              equivalencia entre años.
            </DialogDescription>
          </DialogHeader>
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow className="bg-secondary/50 hover:bg-secondary/50">
                  <TableHead className="text-[11px]">Categoría</TableHead>
                  {isSeries ? (
                    <TableHead className="text-right text-[11px]">
                      2021
                    </TableHead>
                  ) : null}
                  <TableHead className="text-right text-[11px]">
                    {current.year ?? 2024}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activeRows.map((row) => (
                  <TableRow key={row.label}>
                    <TableCell className="max-w-[360px] whitespace-normal text-[12.5px]">
                      {row.label}
                    </TableCell>
                    {isSeries ? (
                      <TableCell className="text-right font-mono text-[12px]">
                        {fmt(row.prior)}
                      </TableCell>
                    ) : null}
                    <TableCell className="text-right font-mono text-[12px]">
                      {fmt(row.current)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <p className="text-[11.5px] leading-relaxed text-muted-foreground">
            {isSeries
              ? `2021 usa ${categories.previous} categorías y 2022 usa ${categories.current}. `
              : `2024 usa ${categories.current} categorías. `}
            {omitted > 0
              ? `Se omiten ${omitted} categorías sin registros en esta ficha. `
              : ""}
            La recodificación impide comparar esta dimensión con las demás
            vistas.
          </p>
        </DialogContent>
      </Dialog>
    </>
  );
}
