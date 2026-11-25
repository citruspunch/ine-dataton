"use client";

import { ExternalLink, ShieldCheck } from "lucide-react";

import { SourcesDialog } from "@/components/sources-dialog";
import { Button } from "@/components/ui/button";
import { basketData, lastDataUpdate } from "@/lib/data";
import { formatNumber, formatUtcStamp } from "@/lib/format";

export function SiteFooter() {
  const meta = basketData.meta;
  const declared = meta.sources.filter(
    (source) => source.license.status === "declarada",
  ).length;
  const undeclared = meta.sources.length - declared;

  return (
    <footer className="mt-2 border-t border-border/80 bg-card/60">
      <div className="mx-auto grid max-w-[1440px] gap-4 px-4 py-5 text-[11px] leading-relaxed text-muted-foreground sm:px-6 lg:grid-cols-[1.5fr_1fr] lg:px-8">
        <div className="space-y-1.5">
          <p className="font-medium text-foreground/90">
            Fuente: Instituto Nacional de Estadística (INE), Guatemala ·{" "}
            <a
              href="https://datos.ine.gob.gt"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-primary underline-offset-2 hover:underline"
            >
              datos.ine.gob.gt
              <ExternalLink className="size-3" />
            </a>
          </p>
          <p>
            {meta.sources.length} archivos oficiales verificados · última
            actualización de datos {formatUtcStamp(lastDataUpdate())} ·{" "}
            {formatNumber(meta.period.count)} meses ({meta.period.firstLabel}–
            {meta.period.lastLabel}).
          </p>
          <p className="flex items-start gap-1.5">
            <ShieldCheck className="mt-0.5 size-3 shrink-0 text-primary" />
            <span>
              Licencias: {declared} conjuntos con licencia declarada (CC BY 4.0,
              serie del IPC) y {undeclared} sin licencia declarada en CKAN
              (costos de la CBA, © INE). Cada archivo tiene URL, fecha UTC de
              descarga y hash SHA-256 en el manifiesto de procedencia.
            </span>
          </p>
        </div>
        <div className="space-y-1.5 lg:text-right">
          <p>
            Cálculos, agrupaciones y visualizaciones propias del equipo
            participante en el <strong className="font-medium">Datatón INE 2026</strong>.
            No son cifras oficiales del INE.
          </p>
          <p>
            Herramienta local, sin servicios en la nube ni claves de API. Uso de
            inteligencia artificial declarado en el README.
          </p>
          <div className="lg:flex lg:justify-end">
            <SourcesDialog
              trigger={
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-[11px] text-primary hover:bg-primary/10 hover:text-primary"
                >
                  Ver procedencia y metodología
                </Button>
              }
            />
          </div>
        </div>
      </div>
    </footer>
  );
}
