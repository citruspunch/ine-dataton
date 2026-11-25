import Link from "next/link";

import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { getJson } from "@/lib/api";
import type { AggregateSummary } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function PublicIndexPage() {
  let snapshot: { snapshot_id: string | null; aggregates: AggregateSummary[] } | null = null;
  let error = "";
  try {
    snapshot = await getJson("/public");
  } catch {
    error = "El motor de validación no está disponible. Arranque `pnpm run dev:engine`.";
  }

  const aggregates = snapshot?.aggregates ?? [];

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          Agregados habilitados para consulta
        </h1>
        <p className="max-w-3xl text-[15px] text-muted">
          Snapshot <span className="font-mono">{snapshot?.snapshot_id ?? "—"}</span>. Solo
          aparecen agregados que pasaron las reglas críticas, tienen licencia verificada y
          recibieron visto bueno humano.
        </p>
      </header>

      {error ? <Alert variant="warn">{error}</Alert> : null}

      {aggregates.length ? (
        <div className="space-y-2">
          {aggregates.map((aggregate) => (
            <div
              key={aggregate.case_id}
              className="flex flex-wrap items-center justify-between gap-4 rounded-md border border-line bg-card px-4 py-3"
            >
              <div>
                <Link
                  href={`/a/${aggregate.case_id}`}
                  className="font-semibold text-brand hover:underline"
                >
                  {aggregate.title || aggregate.label}
                </Link>
                <p className="text-[12.5px] text-muted">
                  <span className="font-mono">{aggregate.case_id}</span> ·{" "}
                  {aggregate.series_count} series · {aggregate.period} · digest{" "}
                  <span className="font-mono">{aggregate.digest.slice(0, 16)}…</span>
                </p>
              </div>
              <div className="flex items-center gap-2">
                {aggregate.synthetic ? <Badge variant="syn">sintético</Badge> : null}
                {aggregate.topic === "ipc" ? <Badge variant="info">IPC</Badge> : null}
                <Badge variant="ok">{aggregate.state_text}</Badge>
                <Link
                  href={`/a/${aggregate.case_id}/ficha`}
                  className={buttonVariants({ variant: "secondary", size: "sm" })}
                >
                  Ficha
                </Link>
                <Link
                  href={`/a/${aggregate.case_id}`}
                  className={buttonVariants({ size: "sm" })}
                >
                  Consultar
                </Link>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>El snapshot público está vacío</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-[13px] text-muted">
              Un agregado solo entra aquí después del gate humano. Use la{" "}
              <Link href="/review" className="text-brand underline">
                bandeja de revisión
              </Link>{" "}
              para habilitar uno.
            </p>
          </CardContent>
        </Card>
      )}

      <section className="space-y-3">
        <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
          Cómo leer esta consulta
        </h2>
        <Table>
          <THead>
            <TR>
              <TH>Lo que sí hace</TH>
              <TH>Lo que no hace</TH>
            </TR>
          </THead>
          <TBody>
            <TR>
              <TD>
                <ul className="list-disc space-y-1 pl-4 text-[13px]">
                  <li>Muestra la cifra publicada por el INE, con su celda de origen.</li>
                  <li>Separa base, periodo y unidad en cada respuesta.</li>
                  <li>Bloquea cruces que no son una variación.</li>
                </ul>
              </TD>
              <TD>
                <ul className="list-disc space-y-1 pl-4 text-[13px]">
                  <li>No calcula cifras nuevas ni empalmes propios.</li>
                  <li>No certifica ni aprueba el dato oficial.</li>
                  <li>No convierte un índice en pobreza, ingreso o crecimiento.</li>
                </ul>
              </TD>
            </TR>
          </TBody>
        </Table>
      </section>
    </div>
  );
}
