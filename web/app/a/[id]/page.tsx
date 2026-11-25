import Link from "next/link";
import { notFound } from "next/navigation";

import { SeverityBadge, StateBadge } from "@/components/badges";
import { Comparator } from "@/components/comparator";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { getJson } from "@/lib/api";
import type { AggregateDetail, Receipt, Series } from "@/lib/types";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function PublicDetailPage({ params }: PageProps) {
  const { id } = await params;

  let payload: { aggregate: AggregateDetail; receipt: Receipt | null } | null = null;
  try {
    payload = await getJson(`/public/${id}`);
  } catch {
    payload = null;
  }
  if (!payload) notFound();

  const { aggregate } = payload;
  const entity = aggregate.entity;
  const series: Series[] = entity.series ?? [];
  const comparable = series.find((item) => item.comparable && item.has_published_variation);
  const defaultSeries = comparable ?? series[0];
  const defaultPeriods = defaultSeries?.points.map((point) => point.period) ?? [];

  return (
    <div className="space-y-6">
      <p className="text-[13px] print:hidden">
        <Link href="/" className="text-brand underline">
          ← Volver al índice de consulta
        </Link>
      </p>

      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">{entity.title}</h1>
        <div className="flex flex-wrap items-center gap-2">
          <StateBadge state={aggregate.state} text={aggregate.state_text} />
          {entity.topic === "ipc" ? <Badge variant="info">IPC</Badge> : null}
          <Badge variant="none">no certifica</Badge>
        </div>
      </header>

      <section className="space-y-3">
        <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
          Ficha técnica
        </h2>
        <dl className="overflow-hidden rounded-md border border-line bg-card text-sm">
          <Row label="Fuente">
            {entity.title} · Instituto Nacional de Estadística (INE)
          </Row>
          <Row label="Periodo">{entity.display.period}</Row>
          <Row label="Base">{entity.display.base}</Row>
          <Row label="Unidad">{entity.display.unit}</Row>
          <Row label="URL de origen">
            <span className="font-mono break-all text-[12px]">{entity.source_url || "—"}</span>
          </Row>
          <Row label="Descargado (UTC)">
            <span className="font-mono">{entity.downloaded_at_utc || "—"}</span>
          </Row>
          <Row label="SHA-256">
            <span className="break-all font-mono">{entity.sha256}</span>
          </Row>
          <Row label="Licencia">
            {entity.license.id || "—"} · {entity.license.attribution || "—"}
          </Row>
          <Row label="Perfil">
            <span className="font-mono">{entity.profile}</span>
          </Row>
          <Row label="Digest de validación">
            <span className="break-all font-mono">{aggregate.digest}</span>
          </Row>
        </dl>
      </section>

      {series.length ? (
        <section className="space-y-3">
          <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
            Comparador seguro de periodos
          </h2>
          <Comparator
            caseId={aggregate.case_id}
            series={series}
            defaults={{
              seriesA: defaultSeries?.series_id ?? "",
              periodA: defaultPeriods[0] ?? "",
              seriesB: defaultSeries?.series_id ?? "",
              periodB: defaultPeriods[defaultPeriods.length - 1] ?? "",
            }}
          />
        </section>
      ) : null}

      {series.length ? (
        <section className="space-y-3">
          <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
            Series publicadas
          </h2>
          <Table>
            <THead>
              <TR>
                <TH>Serie</TH>
                <TH>Etiqueta</TH>
                <TH>Base</TH>
                <TH>Periodos</TH>
                <TH>Comparable</TH>
              </TR>
            </THead>
            <TBody>
              {series.map((item) => (
                <TR key={item.series_id}>
                  <TD className="whitespace-nowrap font-mono">{item.series_id}</TD>
                  <TD>{item.label}</TD>
                  <TD className="whitespace-nowrap">{item.base ?? "—"}</TD>
                  <TD className="whitespace-nowrap">{item.points.length}</TD>
                  <TD>
                    {item.comparable && item.has_published_variation ? (
                      <Badge variant="ok">sí</Badge>
                    ) : (
                      <>
                        <Badge variant="fail">no</Badge>
                        <div className="text-[12px] text-muted">
                          {item.not_comparable_reason ??
                            "sin variación publicada en este recurso"}
                        </div>
                      </>
                    )}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </section>
      ) : null}

      <section className="space-y-3">
        <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
          Reglas evaluadas
        </h2>
        <Table>
          <THead>
            <TR>
              <TH>Regla</TH>
              <TH>Título</TH>
              <TH>Estado</TH>
              <TH>Mensaje</TH>
            </TR>
          </THead>
          <TBody>
            {aggregate.findings.map((finding) => (
              <TR key={finding.rule_id}>
                <TD className="whitespace-nowrap font-mono">{finding.rule_id}</TD>
                <TD>{finding.title}</TD>
                <TD className="whitespace-nowrap">
                  <SeverityBadge status={finding.status} />
                </TD>
                <TD>{finding.message}</TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </section>

      <section className="space-y-3">
        <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
          Recibo y ficha
        </h2>
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={`/a/${aggregate.case_id}/ficha`}
            className={buttonVariants({ variant: "default" })}
          >
            Ficha técnica imprimible
          </Link>
          <Link
            href={`/api/receipt/${aggregate.case_id}`}
            className={buttonVariants({ variant: "secondary" })}
          >
            Descargar recibo.json
          </Link>
        </div>
        <p className="text-[12.5px] text-muted">
          El recibo separa <span className="font-mono">technical_payload</span> y{" "}
          <span className="font-mono">decision_log</span>; el digest no incluye timestamps
          de ejecución ni de decisión.
        </p>
      </section>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[200px_1fr] border-b border-line last:border-0">
      <dt className="bg-[#fafbfc] px-3 py-2 text-[13px] text-muted">{label}</dt>
      <dd className="px-3 py-2">{children}</dd>
    </div>
  );
}
