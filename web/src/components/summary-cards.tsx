"use client";

import {
  ArrowDownRight,
  ArrowUpRight,
  Flame,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  formatKcal,
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
  const official =
    variation === "monthly" ? ipc.officialMonthly : ipc.officialInterannual;
  const directValue =
    variation === "monthly" ? ipc.directMonthly : ipc.directInterannual;
  const crossBase =
    variation === "monthly" ? ipc.crossBaseMonthly : ipc.crossBaseInterannual;
  const invalidDirect = direct && crossBase;
  const displayed = invalidDirect || directValue === null ? official : directValue;
  const positive = displayed >= 0;
  const TrendIcon = positive ? ArrowUpRight : ArrowDownRight;

  return (
    <div className="grid gap-3 sm:grid-cols-[1.4fr_1fr]">
      <Card className="bg-[linear-gradient(145deg,oklch(0.465_0.155_258/0.07),oklch(1_0_0/0)_60%)]">
        <CardContent className="flex h-full flex-col justify-between p-5">
          <div className="flex items-start justify-between gap-3">
            <p className="text-[13px] font-medium text-muted-foreground">
              {mode === "total"
                ? "Costo mensual del hogar"
                : "Costo por 1.000 kcal"}
            </p>
            <Badge
              variant="outline"
              className="border-primary/20 bg-card/80 text-[11px] font-medium text-primary"
            >
              CBA {area.toLowerCase()}
            </Badge>
          </div>

          <div className="mt-4">
            <p className="font-mono text-[40px] font-semibold leading-none tracking-[-0.03em] tabular-nums sm:text-[46px]">
              {mode === "total"
                ? formatQuetzales(householdMonthly)
                : formatQuetzales(month.costPerThousandKcal)}
            </p>
            <p className="mt-3 text-[13.5px] leading-snug text-muted-foreground">
              {mode === "total" ? (
                <>
                  {formatQuetzales(month.dailyCostPerPerson)} por persona al día
                  · {members} {members === 1 ? "integrante" : "integrantes"}
                </>
              ) : (
                <>Eficiencia calórica de la canasta completa</>
              )}
            </p>
          </div>

          <div className="mt-5 flex items-center justify-between gap-3 border-t border-border/70 pt-3 text-[12.5px] text-muted-foreground">
            <span>{month.label}</span>
            <span>
              {mode === "total"
                ? "Incluye agua y sal"
                : "Excluye agua y sal (0 kcal)"}
            </span>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1 lg:grid-rows-2">
        <Card>
          <CardContent className="flex h-full flex-col justify-between p-5">
            <div className="flex items-start justify-between gap-2">
              <p className="text-[13px] font-medium text-muted-foreground">
                Inflación (IPC)
              </p>
              <Badge
                variant="outline"
                className={
                  invalidDirect
                    ? "border-primary/20 bg-primary/[0.06] text-[11px] font-medium text-primary"
                    : "border-border bg-muted/50 text-[11px] font-medium text-muted-foreground"
                }
              >
                {invalidDirect
                  ? "Oficial"
                  : direct
                    ? "Directo"
                    : "Empalme INE"}
              </Badge>
            </div>
            <div className="mt-3">
              <p className="flex items-baseline gap-1.5 font-mono text-[28px] font-semibold leading-none tracking-tight tabular-nums">
                <TrendIcon
                  className={
                    positive
                      ? "size-[18px] self-center text-amber-600"
                      : "size-[18px] self-center text-teal-700"
                  }
                />
                {formatSignedPercent(displayed)}
              </p>
              <p className="mt-1.5 text-[13px] text-muted-foreground">
                {variation === "monthly" ? "Mensual" : "Interanual"} ·{" "}
                {month.label.toLowerCase()}
              </p>
              {invalidDirect ? (
                <p className="mt-1 text-[11.5px] text-amber-800">
                  Directo: {formatSignedPercent(directValue ?? 0)}
                </p>
              ) : null}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex h-full flex-col justify-between p-5">
            <p className="flex items-center gap-1.5 text-[13px] font-medium text-muted-foreground">
              <Flame className="size-3.5 text-primary" />
              Energía de la canasta
            </p>
            <div className="mt-3">
              <p className="font-mono text-[28px] font-semibold leading-none tracking-tight tabular-nums">
                {formatKcal(month.dailyKcalPerPerson)}
              </p>
              <p className="mt-1.5 text-[13px] text-muted-foreground">
                por persona y día · referencia CBA {area.toLowerCase()}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
