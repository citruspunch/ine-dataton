"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, Calculator, CheckCircle2, Info, XCircle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { formatNumber, parsePriceInput } from "@/lib/format";
import type { QueryResult } from "@/lib/types";

export function PriceChecker({ result }: { result: QueryResult }) {
  const [raw, setRaw] = useState("");
  const stats = result.stats;
  const value = useMemo(() => parsePriceInput(raw), [raw]);

  const evaluation = useMemo(() => {
    if (!stats || value === null) return null;
    const difference = stats.median === 0 ? 0 : ((value - stats.median) / stats.median) * 100;
    if (value < stats.min) {
      const gap = stats.min === 0 ? 0 : ((stats.min - value) / stats.min) * 100;
      return {
        tone: "warning" as const,
        title: "Por debajo del mínimo",
        description: `Este valor está ${gap.toFixed(1)}% por debajo del mínimo observado. Verifique la presentación y la fecha.`,
        difference,
      };
    }
    if (value > stats.max) {
      const gap = stats.max === 0 ? 0 : ((value - stats.max) / stats.max) * 100;
      return {
        tone: "destructive" as const,
        title: "Por encima del máximo",
        description: `Este valor está ${gap.toFixed(1)}% por encima del máximo observado. Revise si la presentación es comparable.`,
        difference,
      };
    }
    return {
      tone: "success" as const,
      title: "Dentro del rango observado",
      description:
        value > stats.p75
          ? "Está en el rango, pero por encima del cuartil superior (P75). Úselo con cautela."
          : value < stats.p25
            ? "Está en el rango, pero por debajo del cuartil inferior (P25). Confirme que sea comparable."
            : "Está dentro de la banda central observada para estos filtros.",
      difference,
    };
  }, [stats, value]);

  if (!stats) {
    return (
      <Card className="border-dashed border-border bg-card/60 shadow-none">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 font-heading text-lg">
            <Calculator className="size-4 text-muted-foreground" aria-hidden />
            Verificador
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No hay una banda válida con estos filtros.
          </p>
        </CardContent>
      </Card>
    );
  }

  const isIndex = stats.valueKind === "index";
  const isCost = stats.valueKind === "cost";
  const prefix = isIndex ? "Índice" : "Q";
  const unitLabel = isIndex ? "puntos de índice" : isCost ? "Q por persona al mes" : "Q";

  const fill = (candidate: number) => {
    setRaw(String(Math.round(candidate * 100) / 100));
  };

  return (
    <Card className="border-border/70 bg-card shadow-none">
      <CardHeader className="gap-1.5 pb-4">
        <CardTitle className="flex items-center gap-2 font-heading text-xl">
          <Calculator className="size-5 text-primary" aria-hidden />
          Verificador
        </CardTitle>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Compare un valor con la banda de este filtro.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label
            htmlFor="checker"
            className="mb-1.5 block text-xs font-medium text-muted-foreground"
          >
            Valor a comparar ({unitLabel})
          </label>
          <div className="relative">
            {!isIndex ? (
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 font-mono text-sm text-muted-foreground">
                Q
              </span>
            ) : null}
            <Input
              id="checker"
              inputMode="decimal"
              value={raw}
              onChange={(event) => setRaw(event.target.value)}
              placeholder={isIndex ? "Ej. 104.50" : "Ej. 42.50"}
              className={cn(
                "h-12 rounded-lg border-border bg-background font-mono text-base tabular",
                isIndex ? "pl-3" : "pl-8",
              )}
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
          <Alert className="border-border bg-muted/30">
            <Info className="size-4" aria-hidden />
            <AlertTitle>Ingrese un monto</AlertTitle>
            <AlertDescription>
              Le diremos si está dentro del mínimo y el máximo observados.
            </AlertDescription>
          </Alert>
        ) : null}

        {value === null && raw ? (
          <Alert className="border-border bg-muted/30">
            <Info className="size-4" aria-hidden />
            <AlertTitle>Valor no válido</AlertTitle>
            <AlertDescription>Use solo números, por ejemplo 42.50.</AlertDescription>
          </Alert>
        ) : null}

        {evaluation ? (
          <Alert
            className={cn(
              "border-l-4",
              evaluation.tone === "success" &&
                "border-emerald-300 border-l-emerald-600 bg-emerald-50/70 text-emerald-950",
              evaluation.tone === "warning" &&
                "border-amber-300 border-l-amber-600 bg-amber-50/70 text-amber-950",
              evaluation.tone === "destructive" &&
                "border-destructive/30 border-l-destructive bg-destructive/5 text-destructive",
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
          <p className="text-xs text-muted-foreground">
            Diferencia vs. mediana:{" "}
            <span className="font-mono font-medium text-foreground">
              {evaluation.difference > 0 ? "+" : ""}
              {evaluation.difference.toFixed(1)}%
            </span>
          </p>
        ) : null}

        {stats.unitGroups.length > 1 && !result.selectedUnit ? (
          <p className="flex items-start gap-1.5 text-xs leading-relaxed text-amber-800">
            <AlertTriangle className="mt-0.5 size-3.5 shrink-0" aria-hidden />
            La banda combina varias presentaciones. Elija una para comparar mejor.
          </p>
        ) : null}

        <p className="border-t border-border/60 pt-3 text-xs text-muted-foreground">
          {result.selectedUnit ?? stats.unit} · corte {result.cutoff ?? "sin fecha"} · uso
          informativo, no sustituye una cotización.
        </p>
      </CardContent>
    </Card>
  );
}
