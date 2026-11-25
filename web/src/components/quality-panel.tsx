"use client";

import { ShieldCheck } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatNumber } from "@/lib/format";
import type { QueryResult } from "@/lib/types";

function Count({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="font-mono text-xl font-semibold leading-none tabular">{formatNumber(value)}</div>
      <div className="mt-1 text-xs leading-tight text-muted-foreground">{label}</div>
    </div>
  );
}

export function QualityPanel({ result, includeAlerts }: { result: QueryResult; includeAlerts: boolean }) {
  const quality = result.quality;
  const withAlerts =
    quality.duplicates +
    quality.invalidDate +
    quality.missingDate +
    quality.missingValue +
    quality.missingProduct;
  const hidden = Math.max(0, quality.totalRecords - result.total);

  return (
    <Card className="border-border/70 bg-card shadow-none">
      <CardHeader className="gap-1.5 pb-3">
        <CardTitle className="flex items-center gap-2 font-heading text-lg">
          <ShieldCheck className="size-4 text-primary" aria-hidden />
          Calidad de los datos
        </CardTitle>
        <p className="text-sm leading-relaxed text-muted-foreground">
          {hidden > 0
            ? `${formatNumber(hidden)} registros con alertas están ocultos. Los resúmenes usan solo datos válidos.`
            : withAlerts > 0
              ? `${formatNumber(withAlerts)} registros con alertas en este filtro.`
              : "Sin alertas de fecha, duplicado o valor faltante en este filtro."}
          {hidden > 0 && !includeAlerts ? " Use “Mostrar alertas” para revisarlos." : ""}
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Count label="Duplicados" value={quality.duplicates} />
          <Count label="Precios con comas" value={quality.thousandsComma} />
          <Count label="Sin NOG" value={quality.missingNog} />
          <Count label="Sin precio" value={quality.missingValue} />
        </div>
        <p className="border-t border-border/60 pt-3 text-[13px] leading-relaxed text-muted-foreground">
          En toda la fuente: {formatNumber(result.group.quality.duplicates)} duplicados,{" "}
          {formatNumber(result.group.quality.thousandsComma)} con comas,{" "}
          {formatNumber(result.group.quality.missingNog)} sin NOG,{" "}
          {formatNumber(result.group.quality.invalidDate)} con fecha inválida.
        </p>
      </CardContent>
    </Card>
  );
}
