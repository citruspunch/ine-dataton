"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, Calculator, CheckCircle2, Info, XCircle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { RangeBar } from "@/components/range-bar";
import { cn } from "@/lib/utils";
import { formatNumber, parsePriceInput } from "@/lib/format";
import type { MetricStats, QueryResult } from "@/lib/types";

function percentilePosition(value: number, stats: MetricStats): number {
  if (value <= stats.min) return 0;
  if (value >= stats.max) return 100;
  const interpolate = (lowValue: number, lowPct: number, highValue: number, highPct: number) => {
    if (highValue === lowValue) return lowPct;
    return lowPct + ((value - lowValue) / (highValue - lowValue)) * (highPct - lowPct);
  };
  if (value <= stats.p25) return interpolate(stats.min, 0, stats.p25, 25);
  if (value <= stats.median) return interpolate(stats.p25, 25, stats.median, 50);
  if (value <= stats.p75) return interpolate(stats.median, 50, stats.p75, 75);
  return interpolate(stats.p75, 75, stats.max, 100);
}

export function PriceChecker({ result }: { result: QueryResult }) {
  const [raw, setRaw] = useState("");
  const stats = result.stats;
  const value = useMemo(() => parsePriceInput(raw), [raw]);

  const evaluation = useMemo(() => {
    if (!stats) return null;
    if (value === null) return null;
    const difference = ((value - stats.median) / stats.median) * 100;
    const position = percentilePosition(value, stats);
    if (value < stats.min) {
      return {
        tone: "warning" as const,
        title: "Por debajo del mínimo observado",
        description: `El valor está ${Math.abs(((value - stats.min) / stats.min) * 100).toFixed(1)}% por debajo del mínimo de la banda filtrada. Verifique la presentación y la fecha antes de usarlo.`,
        difference,
        position,
      };
    }
    if (value > stats.max) {
      return {
        tone: "destructive" as const,
        title: "Por encima del máximo observado",
        description: `El valor está ${Math.abs(((value - stats.max) / stats.max) * 100).toFixed(1)}% por encima del máximo de la banda filtrada. Revise si la presentación o la unidad son comparables.`,
        difference,
        position,
      };
    }
    return {
      tone: "success" as const,
      title: "Dentro del rango observado",
      description:
        value > stats.p75
          ? "Está dentro del rango, pero por encima del cuartil superior (P75). Úselo con cautela."
          : value < stats.p25
            ? "Está dentro del rango, pero por debajo del cuartil inferior (P25). Verifique que sea comparable."
            : "Está dentro de la banda central observada para los filtros activos.",
      difference,
      position,
    };
  }, [stats, value]);

  const fill = (candidate: number) => {
    const rounded = Math.round(candidate * 100) / 100;
    setRaw(String(rounded));
  };

  if (!stats) {
    return (
      <Card className="border-dashed border-border bg-card/70">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 font-heading text-lg">
            <Calculator className="size-4 text-muted-foreground" aria-hidden />
            Verificador de precio unitario
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No hay una banda válida con los filtros actuales. Ajuste la búsqueda o la fuente
            para poder comparar un valor.
          </p>
        </CardContent>
      </Card>
    );
  }

  const unitLabel =
    stats.valueKind === "index"
      ? "puntos de índice"
      : stats.valueKind === "cost"
        ? "Q por persona al mes"
        : "Q";
  const prefix = stats.valueKind === "index" ? "Índice" : "Q";

  return (
    <Card className="border-border/80 bg-card/90 shadow-sm">
      <CardHeader className="gap-2 pb-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              Antes de cotizar
            </p>
            <CardTitle className="mt-1 flex items-center gap-2 font-heading text-xl">
              <Calculator className="size-4 text-primary" aria-hidden />
              Verificador unitario
            </CardTitle>
          </div>
          <Badge variant="outline" className="font-normal text-muted-foreground">
            {stats.metric}
          </Badge>
        </div>
        <p className="text-xs leading-relaxed text-muted-foreground">
          Compare un valor contra la banda observada. Se excluyen duplicados, fechas
          inválidas y registros sin precio.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label htmlFor="checker" className="mb-1.5 block text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Valor a comparar ({unitLabel})
          </label>
          <div className="relative">
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              {prefix}
            </span>
            <Input
              id="checker"
              inputMode="decimal"
              value={raw}
              onChange={(event) => setRaw(event.target.value)}
              placeholder={stats.valueKind === "index" ? "Ej. 104.50" : "Ej. 42.50"}
              className="h-11 rounded-xl border-border/90 bg-background/70 pl-12 pr-3 font-mono text-base tabular"
            />
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <Button type="button" size="xs" variant="outline" onClick={() => fill(stats.median)}>
              Mediana
            </Button>
            <Button type="button" size="xs" variant="outline" onClick={() => fill(stats.median * 0.9)}>
              −10%
            </Button>
            <Button type="button" size="xs" variant="outline" onClick={() => fill(stats.median * 1.1)}>
              +10%
            </Button>
            <Button type="button" size="xs" variant="ghost" onClick={() => setRaw("")}>
              Limpiar
            </Button>
          </div>
        </div>

        {value === null && !raw ? (
          <Alert className="border-border/80 bg-muted/30">
            <Info className="size-4" aria-hidden />
            <AlertTitle>Ingrese un monto</AlertTitle>
            <AlertDescription>
              El verificador le dirá si el valor cae dentro del mínimo y el máximo observados,
              y qué tan lejos está de la mediana.
            </AlertDescription>
          </Alert>
        ) : null}

        {evaluation ? (
          <Alert
            className={cn(
              "border-l-4",
              evaluation.tone === "success" && "border-emerald-300/70 border-l-emerald-600 bg-emerald-50/70 text-emerald-950",
              evaluation.tone === "warning" && "border-amber-300/70 border-l-amber-600 bg-amber-50/70 text-amber-950",
              evaluation.tone === "destructive" && "border-destructive/30 border-l-destructive bg-destructive/5 text-destructive",
            )}
          >
            {evaluation.tone === "success" ? (
              <CheckCircle2 className="size-4" aria-hidden />
            ) : evaluation.tone === "warning" ? (
              <AlertTriangle className="size-4" aria-hidden />
            ) : (
              <XCircle className="size-4" aria-hidden />
            )}
            <AlertTitle>{evaluation.title}</AlertTitle>
            <AlertDescription className={cn(evaluation.tone === "destructive" && "text-destructive/90")}>
              {evaluation.description}
            </AlertDescription>
          </Alert>
        ) : null}

        {evaluation ? (
          <div className="rounded-xl border border-border/70 bg-background/60 p-3">
            <div className="flex items-center justify-between text-[10px] text-muted-foreground">
              <span>Mín. {formatNumber(stats.min)}</span>
              <span>Mediana {formatNumber(stats.median)}</span>
              <span>Máx. {formatNumber(stats.max)}</span>
            </div>
            <RangeBar stats={stats} marker={value} className="mt-2" compact />
            <div className="mt-3 grid grid-cols-2 gap-2 text-[10px]">
              <div className="rounded-lg bg-muted/50 px-2 py-1.5">
                <div className="text-muted-foreground">Posición estimada</div>
                <div className="font-mono text-xs font-semibold tabular">
                  percentil {Math.round(evaluation.position)}
                </div>
              </div>
              <div className="rounded-lg bg-muted/50 px-2 py-1.5">
                <div className="text-muted-foreground">Vs. mediana</div>
                <div
                  className={cn(
                    "font-mono text-xs font-semibold tabular",
                    evaluation.difference > 0 ? "text-destructive" : "text-success",
                  )}
                >
                  {evaluation.difference > 0 ? "+" : ""}
                  {evaluation.difference.toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        ) : null}

        {stats.unitGroups.length > 1 && !result.selectedUnit ? (
          <p className="flex items-start gap-1.5 rounded-lg bg-amber-50/70 px-2.5 py-2 text-[10px] leading-relaxed text-amber-900">
            <AlertTriangle className="mt-0.5 size-3 shrink-0" aria-hidden />
            La banda combina {stats.unitGroups.length} presentaciones. Seleccione una
            presentación en los filtros para una comparación más precisa.
          </p>
        ) : null}

        <p className="text-[10px] leading-relaxed text-muted-foreground">
          Referencia: {result.selectedUnit ?? stats.unit} · corte {result.cutoff ?? "sin fecha"}. El
          verificador es una ayuda de lectura; no sustituye una cotización ni un dictamen de
          precios.
        </p>
      </CardContent>
    </Card>
  );
}
