"use client";

import { Info } from "lucide-react";

import { SourcesDialog } from "@/components/sources-dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { basketData } from "@/lib/data";

export function NoticeBanner() {
  const meta = basketData.meta;

  return (
    <Alert className="border-border/80 bg-card px-4 py-3.5">
      <Info className="text-primary" />
      <AlertTitle className="text-[13.5px] font-semibold">
        Datos y método
      </AlertTitle>
      <AlertDescription className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
        <span className="sm:hidden">
          Costos oficiales del INE para la CBA urbana y rural, 2024–2026.{" "}
        </span>
        <span className="hidden sm:inline">
          Costos oficiales del INE para la CBA urbana y rural (
          {meta.period.firstLabel.toLowerCase()} –{" "}
          {meta.period.lastLabel.toLowerCase()}). El gasto mensual usa 30 días y
          el tamaño del hogar; las variaciones del IPC ya incluyen el empalme
          oficial.{" "}
        </span>
        <SourcesDialog
          trigger={
            <button
              type="button"
              className="font-medium text-primary underline-offset-2 hover:underline"
            >
              Ver metodología y fuentes
            </button>
          }
        />
      </AlertDescription>
    </Alert>
  );
}
