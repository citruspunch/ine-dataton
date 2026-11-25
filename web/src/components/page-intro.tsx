import { Badge } from "@/components/ui/badge";
import { formatCompact } from "@/lib/format";
import type { Summary } from "@/lib/types";

export function PageIntro({ summary }: { summary: Summary }) {
  return (
    <section className="pb-6 pt-8 sm:pt-10">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Consulta pre-cotización
          </p>
          <h1 className="mt-2 font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
            Mesa de Precios
          </h1>
          <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-muted-foreground sm:text-base">
            Consulte la banda observada de un producto, su fecha de corte y la calidad del
            registro antes de preparar una cotización.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" className="gap-1.5 font-normal">
            <span className="size-1.5 rounded-full bg-success" />
            Datos oficiales del INE
          </Badge>
          <Badge variant="outline" className="font-normal text-muted-foreground">
            {formatCompact(summary.totalRecords)} observaciones
          </Badge>
        </div>
      </div>
      <p className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
        <span>Precios de referencia</span>
        <span aria-hidden>·</span>
        <span>Índices de construcción</span>
        <span aria-hidden>·</span>
        <span>Canastas básicas</span>
        <span aria-hidden>·</span>
        <span>Sin identificación de proveedores</span>
      </p>
    </section>
  );
}
