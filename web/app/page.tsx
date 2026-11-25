import Link from "next/link";
import {
  ArrowRight,
  BadgeCheck,
  CircleCheck,
  CircleX,
  Database,
  FileText,
  Layers,
  LockKeyhole,
} from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { SectionHeading } from "@/components/page-header";
import { StateBadge } from "@/components/badges";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getJson } from "@/lib/api";
import type { AggregateSummary } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function PublicIndexPage() {
  let snapshot: { snapshot_id: string | null; aggregates: AggregateSummary[] } | null = null;
  try {
    snapshot = await getJson("/public");
  } catch {
    snapshot = null;
  }

  const aggregates = snapshot?.aggregates ?? [];

  return (
    <div className="space-y-10">
      <section className="hairline-grid relative overflow-hidden rounded-2xl border border-line bg-white">
        <div className="relative z-10 max-w-3xl px-6 py-10 sm:px-10 sm:py-12">
          <p className="eyebrow">Consulta pública</p>
          <h1 className="mt-3 text-3xl font-semibold leading-[1.15] tracking-tight text-ink sm:text-[38px]">
            Agregados estadísticos con trazabilidad verificable
          </h1>
          <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-muted">
            Cifras publicadas por el INE que ya pasaron las reglas críticas, tienen una
            licencia verificada y cuentan con una decisión humana registrada. Cada
            respuesta muestra su origen, su base y su huella de validación.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Badge variant="info" className="font-mono">
              snapshot {snapshot?.snapshot_id ?? "no disponible"}
            </Badge>
            <span className="text-[13px] text-muted">
              {aggregates.length}{" "}
              {aggregates.length === 1 ? "agregado habilitado" : "agregados habilitados"}
            </span>
            <Link
              href="/review"
              className={buttonVariants({ variant: "secondary", size: "sm" })}
            >
              <LockKeyhole className="h-3.5 w-3.5" aria-hidden />
              Revisión técnica
            </Link>
          </div>
        </div>
        <div
          aria-hidden
          className="pointer-events-none absolute bottom-8 right-8 hidden h-[58%] w-48 items-end gap-2 opacity-[0.14] sm:flex"
        >
          <div className="h-1/3 flex-1 rounded-t-sm bg-accent" />
          <div className="h-2/3 flex-1 rounded-t-sm bg-accent" />
          <div className="h-full flex-1 rounded-t-sm bg-brand" />
        </div>
      </section>

      {!snapshot ? (
        <Alert variant="warn">
          <Database className="h-4 w-4 shrink-0" aria-hidden />
          <span>
            El motor de validación no está disponible. Verifique que el servicio local esté
            en ejecución y vuelva a cargar la página.
          </span>
        </Alert>
      ) : null}

      <section className="space-y-4">
        <SectionHeading
          title="Agregados habilitados"
          description="Solo aparecen los que completaron el gate humano y mantienen su decisión vigente."
          actions={
            <span className="text-[12.5px] text-muted">
              Actualizado con el snapshot <span className="font-mono">{snapshot?.snapshot_id ?? "—"}</span>
            </span>
          }
        />

        {aggregates.length ? (
          <ul className="divide-y divide-line overflow-hidden rounded-xl border border-line bg-white">
            {aggregates.map((aggregate) => (
              <li key={aggregate.case_id}>
                <div className="flex flex-col gap-4 px-5 py-4 transition-colors hover:bg-[#f8fbfe] sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <Link
                        href={`/a/${aggregate.case_id}`}
                        className="text-[15.5px] font-semibold text-brand hover:underline"
                      >
                        {aggregate.title || aggregate.label}
                      </Link>
                      {aggregate.topic === "ipc" ? (
                        <Badge variant="accent">IPC</Badge>
                      ) : null}
                      <StateBadge state={aggregate.state} text={aggregate.state_text} />
                    </div>
                    <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12.5px] text-muted">
                      <span className="inline-flex items-center gap-1">
                        <Layers className="h-3.5 w-3.5" aria-hidden />
                        {aggregate.series_count}{" "}
                        {aggregate.series_count === 1 ? "serie" : "series"}
                      </span>
                      <span>{aggregate.period ?? "periodo no declarado"}</span>
                      <span className="font-mono text-[11.5px] text-muted/80">
                        {aggregate.case_id}
                      </span>
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Link
                      href={`/a/${aggregate.case_id}/ficha`}
                      className={buttonVariants({ variant: "secondary", size: "sm" })}
                    >
                      <FileText className="h-3.5 w-3.5" aria-hidden />
                      Ficha
                    </Link>
                    <Link
                      href={`/a/${aggregate.case_id}`}
                      className={buttonVariants({ variant: "default", size: "sm" })}
                    >
                      Consultar
                      <ArrowRight className="h-3.5 w-3.5" aria-hidden />
                    </Link>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon={BadgeCheck}
            title="Todavía no hay agregados habilitados"
            action={
              <Link href="/review" className={buttonVariants({ size: "sm" })}>
                Abrir la bandeja de revisión
              </Link>
            }
          >
            Un agregado entra a esta consulta únicamente después de superar las reglas
            críticas y de que un revisor registre su decisión. El snapshot se actualiza en
            cuanto se habilita el primero.
          </EmptyState>
        )}
      </section>

      <section className="space-y-4">
        <SectionHeading title="Cómo leer esta consulta" />
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-ok">
                <CircleCheck className="h-4.5 w-4.5" aria-hidden />
                Lo que sí hace
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2.5 text-[13.5px] leading-relaxed text-ink">
                <li className="flex gap-2">
                  <CircleCheck className="mt-0.5 h-4 w-4 shrink-0 text-ok" aria-hidden />
                  Muestra la cifra publicada por el INE, con su celda de origen.
                </li>
                <li className="flex gap-2">
                  <CircleCheck className="mt-0.5 h-4 w-4 shrink-0 text-ok" aria-hidden />
                  Separa base, periodo y unidad en cada respuesta.
                </li>
                <li className="flex gap-2">
                  <CircleCheck className="mt-0.5 h-4 w-4 shrink-0 text-ok" aria-hidden />
                  Solo publica agregados con una decisión vigente y auditable.
                </li>
              </ul>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-fail">
                <CircleX className="h-4.5 w-4.5" aria-hidden />
                Lo que no hace
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2.5 text-[13.5px] leading-relaxed text-ink">
                <li className="flex gap-2">
                  <CircleX className="mt-0.5 h-4 w-4 shrink-0 text-fail" aria-hidden />
                  No calcula cifras nuevas ni empalmes propios.
                </li>
                <li className="flex gap-2">
                  <CircleX className="mt-0.5 h-4 w-4 shrink-0 text-fail" aria-hidden />
                  No certifica ni aprueba el dato oficial.
                </li>
                <li className="flex gap-2">
                  <CircleX className="mt-0.5 h-4 w-4 shrink-0 text-fail" aria-hidden />
                  No convierte un índice en pobreza, ingreso o crecimiento.
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
