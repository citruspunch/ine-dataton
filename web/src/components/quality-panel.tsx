"use client";

import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, CopyX, Flag, Percent, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { formatNumber } from "@/lib/format";
import type { QueryResult } from "@/lib/types";

function Metric({
  label,
  value,
  tone,
  icon,
  hint,
}: {
  label: string;
  value: number;
  tone: "neutral" | "warning" | "danger";
  icon: ReactNode;
  hint: string;
}) {
  return (
    <div className="flex items-start gap-2.5 rounded-lg border border-border/70 bg-background/50 p-2.5">
      <span
        className={cn(
          "mt-0.5 grid size-6 shrink-0 place-items-center rounded-md",
          tone === "danger" && "bg-destructive/10 text-destructive",
          tone === "warning" && "bg-amber-100 text-amber-700",
          tone === "neutral" && "bg-muted text-muted-foreground",
        )}
      >
        {icon}
      </span>
      <div className="min-w-0">
        <div className="font-mono text-lg font-semibold leading-none tabular">{formatNumber(value)}</div>
        <div className="mt-1 text-[10px] font-medium leading-tight text-foreground/80">{label}</div>
        <div className="mt-0.5 text-[9px] leading-tight text-muted-foreground">{hint}</div>
      </div>
    </div>
  );
}

export function QualityPanel({
  result,
  flaggedOnly,
  onToggleFlagged,
}: {
  result: QueryResult;
  flaggedOnly: boolean;
  onToggleFlagged: () => void;
}) {
  const quality = result.quality;
  const share = quality.totalRecords === 0 ? 0 : (quality.canonicalRecords / quality.totalRecords) * 100;
  const hasFlags =
    quality.invalidDate +
      quality.duplicates +
      quality.thousandsComma +
      quality.missingValue +
      quality.missingDate +
      quality.missingNog +
      quality.missingProduct >
    0;

  return (
    <Card className="border-border/80 bg-card/85">
      <CardHeader className="gap-2 pb-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              Auditoría
            </p>
            <CardTitle className="mt-1 flex items-center gap-2 font-heading text-xl">
              <ShieldCheck className="size-4 text-primary" aria-hidden />
              Salud de los datos
            </CardTitle>
            <p className="mt-1 text-xs text-muted-foreground">
              Filtro actual: {formatNumber(quality.totalRecords)} registros. Los resúmenes usan
              solo observaciones válidas y no duplicadas.
            </p>
          </div>
          <Button
            type="button"
            size="sm"
            variant={flaggedOnly ? "default" : "outline"}
            onClick={onToggleFlagged}
            className="h-8 gap-1.5 rounded-full text-xs"
          >
            <Flag className="size-3" aria-hidden />
            {flaggedOnly ? "Viendo solo alertas" : "Ver solo alertas"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex items-center justify-between text-[10px] text-muted-foreground">
            <span>Entran en resúmenes</span>
            <span className="tabular">
              {formatNumber(quality.canonicalRecords)} / {formatNumber(quality.totalRecords)}
            </span>
          </div>
          <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-success transition-all"
              style={{ width: `${share}%` }}
            />
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          <Metric
            label="Fechas inválidas"
            value={quality.invalidDate}
            tone={quality.invalidDate > 0 ? "danger" : "neutral"}
            icon={<AlertTriangle className="size-3.5" aria-hidden />}
            hint="No entran en los cálculos."
          />
          <Metric
            label="Duplicados"
            value={quality.duplicates}
            tone={quality.duplicates > 0 ? "warning" : "neutral"}
            icon={<CopyX className="size-3.5" aria-hidden />}
            hint="Se conserva la copia más reciente."
          />
          <Metric
            label="Precios con comas"
            value={quality.thousandsComma}
            tone={quality.thousandsComma > 0 ? "warning" : "neutral"}
            icon={<Percent className="size-3.5" aria-hidden />}
            hint="Se convirtieron correctamente."
          />
          <Metric
            label="Sin precio / NOG"
            value={quality.missingValue + quality.missingNog}
            tone={quality.missingValue + quality.missingNog > 0 ? "danger" : "neutral"}
            icon={<Flag className="size-3.5" aria-hidden />}
            hint="Registros señalados para revisión."
          />
        </div>

        <div className="flex items-start gap-2 rounded-lg bg-muted/40 px-3 py-2 text-[10px] leading-relaxed text-muted-foreground">
          {hasFlags ? (
            <AlertTriangle className="mt-0.5 size-3 shrink-0 text-amber-600" aria-hidden />
          ) : (
            <CheckCircle2 className="mt-0.5 size-3 shrink-0 text-success" aria-hidden />
          )}
          <p>
            {flaggedOnly
              ? "La tabla muestra solo registros con alguna alerta; los resúmenes de arriba siguen calculándose sobre las observaciones válidas."
              : hasFlags
                ? "Las alertas son informativas: un precio con comas sigue siendo válido, pero un duplicado o una fecha inválida no entra en la banda. Use “Ver solo alertas” para revisar los casos uno por uno."
                : "No hay alertas de fecha, duplicado, comas o valores faltantes en este filtro."}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 border-t border-border/60 pt-2 text-[10px] text-muted-foreground">
          <span className="font-medium text-foreground/80">En toda la fuente:</span>
          <span>{formatNumber(result.group.quality.duplicates)} duplicados</span>
          <span>·</span>
          <span>{formatNumber(result.group.quality.thousandsComma)} precios con comas</span>
          <span>·</span>
          <span>{formatNumber(result.group.quality.missingNog)} sin NOG</span>
          <span>·</span>
          <span>{formatNumber(result.group.quality.invalidDate)} fechas inválidas</span>
        </div>

        {result.group.status === "frozen" ? (
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="border-amber-300/60 bg-amber-50 text-amber-800">
              Serie congelada
            </Badge>
            <span className="text-[10px] text-muted-foreground">
              Corte {result.group.cutoff ?? "sin fecha"} · no se actualiza mensualmente.
            </span>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
