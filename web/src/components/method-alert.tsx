"use client";

import { AlertTriangle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { basketData } from "@/lib/data";
import {
  formatNumber,
  formatSignedPercent,
  formatSignedPoints,
} from "@/lib/format";
import type { AreaMonth, IpcRow, VariationType } from "@/lib/types";

type MethodAlertProps = {
  visible: boolean;
  ipc: IpcRow;
  month: AreaMonth;
  variation: VariationType;
};

export function MethodAlert({ visible, ipc, month, variation }: MethodAlertProps) {
  if (!visible) return null;

  const meta = basketData.meta;
  const official =
    variation === "monthly" ? ipc.officialMonthly : ipc.officialInterannual;
  const direct =
    variation === "monthly" ? ipc.directMonthly : ipc.directInterannual;
  const gap =
    variation === "monthly" ? ipc.directMonthlyGapPp : ipc.directInterannualGapPp;

  return (
    <Alert
      className="animate-fade-up border-amber-300/80 bg-amber-50/90 px-4 py-3.5 text-amber-950 [&>svg]:text-amber-700"
      aria-live="polite"
    >
      <AlertTriangle />
      <AlertTitle className="text-sm font-semibold">
        Comparación entre bases del IPC no válida
      </AlertTitle>
      <AlertDescription className="mt-1 text-[12px] leading-relaxed text-amber-900/90">
        <p>
          {variation === "monthly" ? (
            <>
              Diciembre de 2024 pertenece a la base diciembre 2023
              (=&nbsp;{formatNumber(meta.splice.dec2024IndexDec2023Base, 6)}) y
              enero de 2025 a la base 2024
              (=&nbsp;{formatNumber(meta.splice.jan2025Index2024Base, 6)}).
              Dividir esos índices directamente mezcla dos escalas.
            </>
          ) : (
            <>
              En {month.year}, la comparación interanual usa un índice de 2025 en
              base 2024 y uno de 2024 en base diciembre 2023. Sin el empalme, la
              variación de 12 meses queda subestimada.
            </>
          )}
        </p>

        <div className="mt-2.5 grid gap-2 sm:grid-cols-3">
          <div className="rounded-lg border border-emerald-300/70 bg-white/70 px-2.5 py-2">
            <p className="text-[9.5px] font-semibold uppercase tracking-wide text-emerald-800">
              Oficial empalmado
            </p>
            <p className="mt-0.5 font-mono text-base font-semibold text-emerald-950">
              {formatSignedPercent(official)}
            </p>
          </div>
          <div className="rounded-lg border border-amber-300 bg-white/60 px-2.5 py-2">
            <p className="text-[9.5px] font-semibold uppercase tracking-wide text-amber-800">
              Cálculo directo · inválido
            </p>
            <p className="mt-0.5 font-mono text-base font-semibold text-amber-950">
              {formatSignedPercent(direct ?? 0)}
            </p>
          </div>
          <div className="rounded-lg border border-amber-300/70 bg-white/60 px-2.5 py-2">
            <p className="text-[9.5px] font-semibold uppercase tracking-wide text-amber-800">
              Diferencia
            </p>
            <p className="mt-0.5 font-mono text-base font-semibold text-amber-950">
              {gap !== null ? formatSignedPoints(gap) : "—"}
            </p>
          </div>
        </div>

        <p className="mt-2.5">
          El factor de enlace oficial 2023→2024 es{" "}
          <span className="font-mono font-semibold">
            {formatNumber(meta.splice.linkFactor2023To2024, 6)}
          </span>
          . La aplicación presenta siempre la cifra del empalme del INE. Además,
          la canasta 2024–2026 no es comparable con la CBA anterior a 2024 por el
          cambio metodológico.
        </p>
      </AlertDescription>
    </Alert>
  );
}
