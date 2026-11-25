import Link from "next/link";
import { notFound } from "next/navigation";

import { SeverityBadge, StateBadge } from "@/components/badges";
import { PrintButton } from "@/components/print-button";
import { buttonVariants } from "@/components/ui/button";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { getJson } from "@/lib/api";
import type { AggregateDetail, Receipt } from "@/lib/types";
import { formatPct } from "@/lib/utils";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function FichaPage({ params }: PageProps) {
  const { id } = await params;

  let payload: { aggregate: AggregateDetail; receipt: Receipt | null } | null = null;
  try {
    payload = await getJson(`/public/${id}`);
  } catch {
    payload = null;
  }
  if (!payload) notFound();

  const { aggregate, receipt } = payload;
  const entity = aggregate.entity;
  const decision = receipt?.decision_log as Record<string, string> | null | undefined;
  const rulesVersion = (receipt?.technical_payload as Record<string, unknown> | undefined)
    ?.rules_version as string | undefined;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3 print:hidden">
        <Link
          href={`/a/${aggregate.case_id}`}
          className={buttonVariants({ variant: "secondary" })}
        >
          ← Volver a la consulta
        </Link>
        <PrintButton />
        <Link
          href={`/api/receipt/${aggregate.case_id}`}
          className={buttonVariants({ variant: "secondary" })}
        >
          recibo.json
        </Link>
      </div>

      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          Ficha técnica de validación
        </h1>
        <p className="text-[13px] text-muted">
          Documento para adjuntar al ticket de publicación (procedimiento 18, pasos 4 a 6,
          como propuesta). No certifica el dato ni sustituye la revisión del productor.
        </p>
      </header>

      <dl className="overflow-hidden rounded-md border border-line bg-card text-sm">
        <Row label="Agregado">{entity.title}</Row>
        <Row label="Identificador">
          <span className="font-mono">{aggregate.case_id}</span>
        </Row>
        <Row label="Snapshot">
          <span className="font-mono">
            {(receipt?.technical_payload as Record<string, unknown>)?.snapshot_id as string}
          </span>
        </Row>
        <Row label="Periodo">{entity.display.period}</Row>
        <Row label="Base">{entity.display.base}</Row>
        <Row label="Unidad">{entity.display.unit}</Row>
        <Row label="URL oficial">
          <span className="break-all font-mono text-[12px]">{entity.source_url || "—"}</span>
        </Row>
        <Row label="Descargado (UTC)">
          <span className="font-mono">{entity.downloaded_at_utc || "—"}</span>
        </Row>
        <Row label="SHA-256 del archivo">
          <span className="break-all font-mono">{entity.sha256}</span>
        </Row>
        <Row label="Licencia">
          {entity.license.id || "—"} · {entity.license.attribution || "—"}
        </Row>
        <Row label="Perfil declarativo">
          <span className="font-mono">{entity.profile}</span>
        </Row>
        <Row label="Versión de reglas">
          <span className="font-mono">{rulesVersion ?? "—"}</span>
        </Row>
        <Row label="Digest de validación">
          <span className="break-all font-mono">{aggregate.digest}</span>
        </Row>
        <Row label="Estado">
          <StateBadge state={aggregate.state} text={aggregate.state_text} />
        </Row>
      </dl>

      <section className="space-y-2">
        <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
          Resultado por regla
        </h2>
        <Table>
          <THead>
            <TR>
              <TH>Regla</TH>
              <TH>Título</TH>
              <TH>Estado</TH>
              <TH>Crítica</TH>
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
                <TD className="whitespace-nowrap">{finding.critical ? "sí" : "no"}</TD>
                <TD>{finding.message}</TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </section>

      {aggregate.comparisons.length ? (
        <section className="space-y-2">
          <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
            Comparaciones evaluadas
          </h2>
          <Table>
            <THead>
              <TR>
                <TH>Solicitud</TH>
                <TH>Resultado</TH>
                <TH>Motivo</TH>
                <TH>Dato mostrado</TH>
              </TR>
            </THead>
            <TBody>
              {aggregate.comparisons.map((comparison) => {
                const evidence = (comparison.evidence ?? {}) as Record<string, unknown>;
                return (
                  <TR key={comparison.comparison_id}>
                    <TD>{comparison.label}</TD>
                    <TD className="whitespace-nowrap">{comparison.status}</TD>
                    <TD>{comparison.reason}</TD>
                    <TD className="whitespace-nowrap">
                      {comparison.status === "ok" ? (
                        <>
                          {formatPct(evidence.published_pct as number)}{" "}
                          <span className="font-mono text-[11.5px] text-muted">
                            {String(evidence.published_cell ?? "")}
                          </span>
                        </>
                      ) : (
                        "no se muestra valor"
                      )}
                    </TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
        </section>
      ) : null}

      <section className="space-y-2">
        <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
          Decisión registrada
        </h2>
        {decision ? (
          <dl className="overflow-hidden rounded-md border border-line bg-card text-sm">
            <Row label="Resultado del gate">{decision.gate_decision}</Row>
            <Row label="Responsable">{decision.operator}</Row>
            <Row label="Fecha (UTC)">
              <span className="font-mono">{decision.decided_at_utc}</span>
            </Row>
            <Row label="Motivo">{decision.rationale}</Row>
            <Row label="Digest de la decisión">
              <span className="break-all font-mono">{decision.decision_basis_digest}</span>
            </Row>
          </dl>
        ) : (
          <p className="text-[13px] text-muted">Sin decisión registrada en el recibo público.</p>
        )}
      </section>

      <div className="grid gap-8 pt-4 sm:grid-cols-2">
        <div>
          <p className="mb-8 text-[13px] text-muted">Revisado por (publicaciones)</p>
          <div className="border-t border-[#999] pt-1 text-[12px]">Nombre y firma</div>
        </div>
        <div>
          <p className="mb-8 text-[13px] text-muted">Aprobado por (producción)</p>
          <div className="border-t border-[#999] pt-1 text-[12px]">Nombre y firma</div>
        </div>
      </div>

      <p className="text-[12px] text-muted">
        La habilitación es del prototipo, no del INE. Este documento no certifica. El digest
        no incluye timestamps de ejecución ni de decisión. Los datos conservan su licencia{" "}
        {entity.license.id || "original"}.
      </p>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[210px_1fr] border-b border-line last:border-0 print:grid-cols-[180px_1fr]">
      <dt className="bg-[#fafbfc] px-3 py-2 text-[13px] text-muted">{label}</dt>
      <dd className="px-3 py-2">{children}</dd>
    </div>
  );
}
