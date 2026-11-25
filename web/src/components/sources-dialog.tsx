"use client";

import { ExternalLink, FileSpreadsheet, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { formatUtc, truncateMiddle } from "@/lib/format";
import type { Meta } from "@/lib/types";

export function SourcesDialog({
  meta,
  open,
  onOpenChange,
}: {
  meta: Meta;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[86vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle className="text-lg">Fuentes y metodología</DialogTitle>
          <DialogDescription className="text-[13px]">
            Datos abiertos del Instituto Nacional de Estadística (INE). Cada
            archivo registra URL, fecha UTC, SHA-256 y licencia.
          </DialogDescription>
        </DialogHeader>

        <section className="space-y-2">
          <h3 className="text-[13px] font-semibold">Fuentes</h3>
          <div className="divide-y rounded-lg border">
            {meta.sources.map((source) => (
              <div key={source.key} className="space-y-1 p-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="flex min-w-0 items-center gap-2">
                    <FileSpreadsheet className="size-3.5 shrink-0 text-primary" />
                    <span className="text-[12.5px] font-medium">
                      {source.title}
                    </span>
                  </div>
                  <Badge
                    variant="outline"
                    className="h-5 rounded-full border-teal-200 bg-teal-50 px-2 text-[10px] font-medium text-teal-900"
                  >
                    CC BY
                  </Badge>
                </div>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-start gap-1 break-all text-[11.5px] leading-relaxed text-primary hover:underline"
                >
                  <ExternalLink className="mt-0.5 size-3 shrink-0" />
                  {source.url}
                </a>
                <p className="text-[11.5px] text-muted-foreground">
                  Descargado {formatUtc(source.downloaded_at_utc)} · SHA-256{" "}
                  <span className="font-mono">
                    {truncateMiddle(source.sha256, 12, 8)}
                  </span>
                </p>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2">
          <div>
            <h3 className="text-[13px] font-semibold">Cómo leer las cifras</h3>
            <ul className="mt-2 space-y-2 text-[12px] leading-relaxed text-muted-foreground">
              <li>
                <span className="font-medium text-foreground">Población:</span>{" "}
                stock del Censo 2018, no una proyección a 2024.
              </li>
              <li>
                <span className="font-medium text-foreground">
                  Establecimientos:
                </span>{" "}
                registros DINESE. No hay empleo, ventas ni identificadores de
                empresa.
              </li>
              <li>
                <span className="font-medium text-foreground">
                  Comparabilidad:
                </span>{" "}
                2024 es un corte transversal; la serie solo se lee entre 2021 y
                2022.
              </li>
            </ul>
          </div>
          <div>
            <h3 className="text-[13px] font-semibold">Límites</h3>
            <ul className="mt-2 space-y-2 text-[12px] leading-relaxed text-muted-foreground">
              {meta.limitations.slice(0, 4).map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </div>
        </section>

        <div className="flex items-start gap-2 rounded-lg bg-secondary/50 p-3 text-[11.5px] leading-relaxed text-muted-foreground">
          <ShieldCheck className="mt-0.5 size-3.5 shrink-0 text-primary" />
          <span>
            Solo agregados municipio × sección CIIU, tamaño y personería. Sin
            microdatos, nombres de empresas ni personas. Secreto estadístico
            conforme al Decreto-Ley 3-85.
          </span>
        </div>

        <div className="sticky bottom-0 z-10 -mx-4 -mb-4 flex items-center justify-between gap-3 border-t bg-popover px-4 py-3">
          <p className="text-[10.5px] leading-tight text-muted-foreground">
            Generado {formatUtc(meta.generated_at_utc)}
            <span className="hidden sm:inline"> · pipeline v{meta.pipeline_version}</span>
          </p>
          <div className="flex shrink-0 gap-2">
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-1.5 text-[12px]"
              onClick={() =>
                window.open(
                  "/data/manifest.json",
                  "_blank",
                  "noopener,noreferrer",
                )
              }
            >
              Manifiesto
              <ExternalLink className="size-3" />
            </Button>
            <DialogClose render={<Button size="sm" className="h-8 text-[12px]" />}>
              Cerrar
            </DialogClose>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
