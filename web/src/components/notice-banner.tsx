"use client";

import { CalendarRange, Flame, GitMerge, Info, Users } from "lucide-react";

import { SourcesDialog } from "@/components/sources-dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { basketData, lastDataUpdate } from "@/lib/data";
import { formatNumber, formatUtcStamp } from "@/lib/format";

const FACTS = [
  {
    icon: CalendarRange,
    title: "CBA 2024–2026",
    text: "Nueva metodología (ENCOVI 2023); no comparable con canastas previas a 2024.",
  },
  {
    icon: Users,
    title: "Costo diario × 30 × hogar",
    text: "Se usa el costo per cápita publicado y se escala por 1 a 8 integrantes.",
  },
  {
    icon: GitMerge,
    title: "Empalme oficial del IPC",
    text: "Las variaciones vienen del empalme del INE; no se encadenan bases sin enlace.",
  },
  {
    icon: Flame,
    title: "0 kcal fuera del cálculo",
    text: "En el modo Q/1.000 kcal se excluyen el agua purificada y la sal.",
  },
];

export function NoticeBanner() {
  const meta = basketData.meta;

  return (
    <Alert className="relative overflow-hidden border-primary/20 bg-[linear-gradient(100deg,oklch(0.465_0.155_258/0.055),oklch(0.735_0.145_78/0.07))] px-4 py-3.5 sm:px-5">
      <Info className="text-primary" />
      <div className="col-start-2 flex flex-wrap items-start justify-between gap-2">
        <div>
          <AlertTitle className="text-sm font-semibold">
            Aviso metodológico
          </AlertTitle>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Costos per cápita y variaciones del IPC calculados con datos
            oficiales del INE, {meta.period.firstLabel} a {meta.period.lastLabel}{" "}
            ({meta.period.count} meses).
          </p>
        </div>
        <SourcesDialog
          trigger={
            <Button
              variant="ghost"
              size="sm"
              className="h-7 shrink-0 px-2 text-xs font-medium text-primary hover:bg-primary/10 hover:text-primary"
            >
              Ver metodología y fuentes
            </Button>
          }
        />
      </div>
      <AlertDescription className="col-start-2 mt-2.5">
        <div className="mb-2 flex flex-wrap gap-1.5 sm:hidden">
          {FACTS.map((fact) => (
            <span
              key={fact.title}
              className="inline-flex items-center gap-1 rounded-full border border-border/70 bg-card/80 px-2 py-1 text-[10px] font-medium text-foreground/80"
            >
              <fact.icon className="size-3 text-primary" />
              {fact.title}
            </span>
          ))}
        </div>
        <ul className="hidden gap-2 sm:grid sm:grid-cols-2 xl:grid-cols-4">
          {FACTS.map((fact) => (
            <li
              key={fact.title}
              className="flex items-start gap-2 rounded-lg border border-border/60 bg-card/70 px-2.5 py-2"
            >
              <fact.icon className="mt-0.5 size-3.5 shrink-0 text-primary" />
              <div className="min-w-0">
                <p className="text-[11px] font-semibold leading-snug text-foreground">
                  {fact.title}
                </p>
                <p className="mt-0.5 text-[11px] leading-snug text-muted-foreground">
                  {fact.text}
                </p>
              </div>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-[10.5px] leading-relaxed text-muted-foreground/90">
          Fuente: Instituto Nacional de Estadística (INE) ·{" "}
          <a
            href="https://datos.ine.gob.gt"
            target="_blank"
            rel="noreferrer"
            className="text-primary underline-offset-2 hover:underline"
          >
            datos.ine.gob.gt
          </a>{" "}
          · descarga {formatUtcStamp(lastDataUpdate())} · licencias: CC BY 4.0
          (IPC) y sin licencia declarada en CKAN (CBA, © INE). Referencias:{" "}
          {formatNumber(meta.areas.Urbana.referenceKcal)} kcal/día urbanas y{" "}
          {formatNumber(meta.areas.Rural.referenceKcal)} kcal/día rurales por
          persona. Cálculos propios; no son cifras oficiales del INE.
        </p>
      </AlertDescription>
    </Alert>
  );
}
