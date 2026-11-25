"use client";

import { Info } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export function MethodologyBreakAlert({ visible }: { visible: boolean }) {
  if (!visible) return null;

  return (
    <Alert className="border-border/80 bg-muted/40 px-4 py-3 [&>svg]:text-primary">
      <Info />
      <AlertTitle className="text-[13px] font-semibold">
        Serie comparable desde enero 2024
      </AlertTitle>
      <AlertDescription className="mt-0.5 text-[12.5px] leading-relaxed text-muted-foreground">
        La CBA 2024–2026 usa una metodología nueva. Los periodos anteriores no
        son comparables y no se ofrecen en el simulador.
      </AlertDescription>
    </Alert>
  );
}
