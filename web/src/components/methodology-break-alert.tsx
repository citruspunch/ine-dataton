"use client";

import { Info } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { basketData } from "@/lib/data";

export function MethodologyBreakAlert({ visible }: { visible: boolean }) {
  if (!visible) return null;
  const meta = basketData.meta;

  return (
    <Alert className="border-primary/20 bg-primary/[0.035] px-4 py-3 [&>svg]:text-primary">
      <Info />
      <AlertTitle className="text-[13px] font-semibold">
        Inicio de la serie comparable · {meta.period.firstLabel}
      </AlertTitle>
      <AlertDescription className="mt-0.5 text-[11.5px] leading-relaxed text-muted-foreground">
        La CBA 2024–2026 inaugura la metodología basada en la ENCOVI 2023. Los
        periodos anteriores a 2024 no son comparables con esta canasta y el
        simulador no los ofrece: cualquier serie que los cruce mezclaría dos
        metodologías distintas.
      </AlertDescription>
    </Alert>
  );
}
