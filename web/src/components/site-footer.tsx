"use client";

import { ExternalLink } from "lucide-react";

import { SourcesDialog } from "@/components/sources-dialog";
import { lastDataUpdate } from "@/lib/data";
import { formatUtcStamp } from "@/lib/format";

export function SiteFooter() {
  return (
    <footer className="border-t border-border/70">
      <div className="mx-auto flex max-w-[1180px] flex-col gap-1.5 px-5 py-6 text-[12.5px] leading-relaxed text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <p>
          Fuente:{" "}
          <a
            href="https://datos.ine.gob.gt"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-foreground/80 underline-offset-2 hover:text-primary hover:underline"
          >
            Instituto Nacional de Estadística (INE)
            <ExternalLink className="size-3" />
          </a>{" "}
          · datos descargados el {formatUtcStamp(lastDataUpdate())}
        </p>
        <p className="flex flex-wrap items-center gap-x-1.5 gap-y-1">
          <span>Cálculos propios, no son cifras oficiales del INE.</span>
          <SourcesDialog
            trigger={
              <button
                type="button"
                className="font-medium text-foreground/80 underline-offset-2 hover:text-primary hover:underline"
              >
                Fuentes y licencias
              </button>
            }
          />
        </p>
      </div>
    </footer>
  );
}
