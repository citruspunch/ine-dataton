import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { MethodNotes } from "@/components/method-notes";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { SourcesView } from "@/components/sources-view";
import { loadDictionary, loadManifest, loadSummary } from "@/lib/data";
import { formatCompact } from "@/lib/format";

export const metadata: Metadata = {
  title: "Fuentes y método | Mesa de Precios",
  description:
    "URLs oficiales, cortes, hashes, licencias y límites de los datos del INE usados en Mesa de Precios.",
};

export default function FuentesPage() {
  const summary = loadSummary();
  const manifest = loadManifest();
  const dictionary = loadDictionary();

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <header className="py-10">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="size-4" aria-hidden />
              Volver a la consulta
            </Link>
            <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Trazabilidad
                </p>
                <h1 className="mt-2 font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
                  Fuentes y método
                </h1>
                <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-muted-foreground">
                  De dónde sale cada cifra, qué fecha tiene y qué se puede concluir. Los
                  archivos se descargan de URLs oficiales del INE y se verifican con SHA-256.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline" className="font-normal">
                  {manifest.datasets.length} archivos
                </Badge>
                <Badge variant="outline" className="font-normal text-muted-foreground">
                  {formatCompact(summary.totalRecords)} observaciones
                </Badge>
              </div>
            </div>
          </header>

          <SourcesView manifest={manifest} />
          <MethodNotes dictionary={dictionary} manifest={manifest} />
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
