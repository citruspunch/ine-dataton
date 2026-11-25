"use client";

import { AlertTriangle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { formatSignedPercent } from "@/lib/format";
import type { AreaMonth, IpcRow, VariationType } from "@/lib/types";

type MethodAlertProps = {
  visible: boolean;
  ipc: IpcRow;
  month: AreaMonth;
  variation: VariationType;
};

export function MethodAlert({ visible, ipc, month, variation }: MethodAlertProps) {
  if (!visible) return null;

  const official =
    variation === "monthly" ? ipc.officialMonthly : ipc.officialInterannual;
  const direct =
    variation === "monthly" ? ipc.directMonthly : ipc.directInterannual;

  return (
    <Alert
      className="animate-fade-up border-amber-300/80 bg-amber-50 px-4 py-3.5 text-amber-950 [&>svg]:text-amber-700"
      aria-live="polite"
    >
      <AlertTriangle />
      <AlertTitle className="text-[13.5px] font-semibold">
        No se pueden comparar bases del IPC sin empalme
      </AlertTitle>
      <AlertDescription className="mt-1 text-[13px] leading-relaxed text-amber-900/90">
        En {month.label.toLowerCase()}, el cálculo directo mezcla índices de
        bases distintas y daría{" "}
        <strong className="font-semibold">{formatSignedPercent(direct ?? 0)}</strong>
        ; la cifra oficial del INE es{" "}
        <strong className="font-semibold">{formatSignedPercent(official)}</strong>
        . La aplicación muestra siempre la cifra empalmada. La CBA 2024–2026
        tampoco es comparable con canastas anteriores a 2024.
      </AlertDescription>
    </Alert>
  );
}
