"use client";

import {
  ArrowDownRight,
  ArrowUpRight,
  Flame,
  Info,
  TrendingUp,
  Wallet,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  formatKcal,
  formatNumber,
  formatPercent,
  formatQuetzales,
  formatSignedPercent,
} from "@/lib/format";
import type { Area, AreaMonth, IpcRow, Mode, VariationType } from "@/lib/types";

type SummaryCardsProps = {
  area: Area;
  mode: Mode;
  month: AreaMonth;
  members: number;
  ipc: IpcRow;
  variation: VariationType;
  direct: boolean;
};

function VariationBadge({
  direct,
  invalid,
}: {
  direct: boolean;
  invalid: boolean;
}) {
  if (!direct) {
    return (
      <Badge
        variant="outline"
        className="gap-1 border-primary/25 bg-primary/[0.06] text-[10px] font-medium text-primary"
      >
        <Info className="size-2.5" />
        Empalme INE
      </Badge>
    );
  }
  if (invalid) {
    return (
      <Badge
        variant="destructive"
        className="gap-1 text-[10px] font-medium"
      >
        Cifra oficial
      </Badge>
    );
  }
  return (
    <Badge
      variant="outline"
      className="gap-1 border-border bg-muted/60 text-[10px] font-medium text-muted-foreground"
    >
      Directo válido
    </Badge>
  );
}

export function SummaryCards({
  area,
  mode,
  month,
  members,
  ipc,
  variation,
  direct,
}: SummaryCardsProps) {
  const householdMonthly = month.monthlyCostPerPerson * members;
  const householdDailyKcal = month.dailyKcalPerPerson * members;
  const official =
    variation === "monthly" ? ipc.officialMonthly : ipc.officialInterannual;
  const directValue =
    variation === "monthly" ? ipc.directMonthly : ipc.directInterannual;
  const crossBase =
    variation === "monthly" ? ipc.crossBaseMonthly : ipc.crossBaseInterannual;
  const gap =
    variation === "monthly" ? ipc.directMonthlyGapPp : ipc.directInterannualGapPp;
  const invalidDirect = direct && crossBase;
  const displayed = invalidDirect || directValue === null ? official : directValue;
  const isPositive = displayed >= 0;
  const TrendIcon = isPositive ? ArrowUpRight : ArrowDownRight;

  const variationLabel =
    variation === "monthly" ? "Mensual" : "Interanual (12 meses)";

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      <Card className="relative overflow-hidden bg-[linear-gradient(140deg,oklch(0.465_0.155_258/0.075),oklch(1_0_0/0)_62%)]">
        <CardHeader className="pb-1">
          <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <Wallet className="size-3.5 text-primary" />
            {mode === "total" ? "Costo mensual del hogar" : "Costo por 1.000 kcal"}
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-2">
          <p className="font-mono text-[30px] font-semibold leading-none tracking-tight tabular-nums sm:text-[32px]">
            {mode === "total"
              ? formatQuetzales(householdMonthly)
              : formatQuetzales(month.costPerThousandKcal)}
          </p>
          <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
            {mode === "total" ? (
              <>
                {formatQuetzales(month.dailyCostPerPerson)} por persona y día ·{" "}
                {members} {members === 1 ? "integrante" : "integrantes"}
              </>
            ) : (
              <>
                Canasta de {formatNumber(month.dailyKcalPerPerson)} kcal diarias ·{" "}
                {area.toLowerCase()}
              </>
            )}
          </p>
        </CardContent>
        <CardFooter className="mt-auto justify-between gap-2 bg-transparent py-2.5 text-[10.5px] text-muted-foreground">
          {mode === "total" ? (
            <>
              <span>
                Incluye {formatQuetzales(month.excludedCostPerPersonDay)}/día de
                agua y sal
              </span>
              <span className="font-mono">
                {formatQuetzales(month.monthlyCostPerPerson)} × {members}
              </span>
            </>
          ) : (
            <>
              <span>
                Excluye {formatQuetzales(month.excludedCostPerPersonDay)}/día de
                agua y sal
              </span>
              <span className="font-mono">0 kcal</span>
            </>
          )}
        </CardFooter>
      </Card>

      <Card>
        <CardHeader className="pb-1">
          <CardTitle className="flex items-center justify-between gap-2 text-xs font-medium text-muted-foreground">
            <span className="inline-flex items-center gap-2">
              <TrendingUp className="size-3.5 text-primary" />
              Variación del IPC
            </span>
            <VariationBadge direct={direct} invalid={invalidDirect} />
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-2">
          <p className="flex items-baseline gap-1.5 font-mono text-[30px] font-semibold leading-none tracking-tight tabular-nums sm:text-[32px]">
            <TrendIcon
              className={
                isPositive
                  ? "size-5 self-center text-amber-600"
                  : "size-5 self-center text-teal-700"
              }
            />
            {formatSignedPercent(displayed)}
          </p>
          <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
            {variationLabel} · {month.label}
            {invalidDirect ? (
              <span className="mt-1 block text-amber-800">
                Cálculo directo: {formatSignedPercent(directValue ?? 0)} (
                {gap !== null ? `${formatNumber(Math.abs(gap), 2)} pp` : "—"} de
                diferencia)
              </span>
            ) : null}
          </p>
        </CardContent>
        <CardFooter className="mt-auto justify-between gap-2 bg-transparent py-2.5 text-[10.5px] text-muted-foreground">
          <span>
            Acumulada {ipc.year}: {formatPercent(ipc.officialAccumulated)}
          </span>
          <span className="font-mono">
            {invalidDirect ? "oficial empalmada" : direct ? "directo" : "empalme INE"}
          </span>
        </CardFooter>
      </Card>

      <Card className="sm:col-span-2 xl:col-span-1">
        <CardHeader className="pb-1">
          <CardTitle className="flex items-center justify-between gap-2 text-xs font-medium text-muted-foreground">
            <span className="inline-flex items-center gap-2">
              <Flame className="size-3.5 text-primary" />
              Cobertura calórica
            </span>
            <Badge
              variant="outline"
              className="border-border bg-muted/60 text-[10px] text-muted-foreground"
            >
              CBA {area.toLowerCase()}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-2">
          <p className="font-mono text-[30px] font-semibold leading-none tracking-tight tabular-nums sm:text-[32px]">
            {formatKcal(month.dailyKcalPerPerson)}
          </p>
          <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
            por persona y día ·{" "}
            {formatNumber(month.coveragePct, 0)} % de la referencia de la canasta
          </p>
        </CardContent>
        <CardFooter className="mt-auto justify-between gap-2 bg-transparent py-2.5 text-[10.5px] text-muted-foreground">
          <span>{formatKcal(householdDailyKcal)} para el hogar</span>
          <span className="font-mono">
            {formatNumber(month.dailyKcalPerPerson)} × {members}
          </span>
        </CardFooter>
      </Card>
    </div>
  );
}
