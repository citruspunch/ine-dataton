import Link from "next/link";
import { notFound } from "next/navigation";

import { simulate, undoSimulation } from "@/app/actions";
import { SeverityBadge, StateBadge } from "@/components/badges";
import { GateForm } from "@/components/gate-form";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { getJson } from "@/lib/api";
import type { ReviewPayload } from "@/lib/types";
import { formatPct } from "@/lib/utils";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ msg?: string; kind?: string }>;
}

export default async function ReviewDetailPage({ params, searchParams }: PageProps) {
  const { id } = await params;
  const query = await searchParams;

  let data: ReviewPayload | null = null;
  try {
    data = await getJson<ReviewPayload>(`/review/${id}`);
  } catch {
    data = null;
  }
  if (!data) notFound();

  const entity = data.entity;
  const isPair = entity.kind === "par de recursos";

  return (
    <div className="space-y-6">
      <p className="text-[13px]">
        <Link href="/review" className="text-brand underline">
          ← Volver a la bandeja
        </Link>
      </p>

      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">{data.label}</h1>
        <div className="flex flex-wrap items-center gap-2">
          <StateBadge state={data.state} text={data.state_text} />
          <Badge variant={data.published ? "ok" : "none"}>
            {data.published ? "publicado en consulta" : "no publicado"}
          </Badge>
          <Badge variant="info">
            {data.coverage.critical_evaluated}/{data.coverage.critical_total} críticas
            evaluadas
          </Badge>
          {data.override ? <Badge variant="warn">simulación activa</Badge> : null}
        </div>
      </header>

      {query.msg ? (
        <Alert variant={query.kind === "err" ? "fail" : query.kind === "warn" ? "warn" : "ok"}>
          {query.msg}
        </Alert>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="space-y-3">
          <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
            Ficha
          </h2>
          <dl className="overflow-hidden rounded-md border border-line bg-card text-sm">
            {isPair ? (
              <>
                <Row label="Recursos">
                  {(entity.resources ?? []).map((resource) => (
                    <div key={resource.manifest_item}>
                      <span className="font-mono">{resource.manifest_item}</span> ·{" "}
                      {resource.identity.dataset} · {resource.identity.period}
                    </div>
                  ))}
                </Row>
                <Row label="Mismos bytes">{entity.same_bytes ? "sí" : "no"}</Row>
                <Row label="SHA-256">
                  <span className="font-mono break-all">{entity.sha256}</span>
                </Row>
              </>
            ) : (
              <>
                <Row label="Fuente">{entity.title}</Row>
                <Row label="Origen">
                  {entity.origin === "upload"
                    ? "archivo cargado en la sesión"
                    : "snapshot del repositorio"}
                </Row>
                <Row label="Periodo">{entity.display.period}</Row>
                <Row label="Base">{entity.display.base}</Row>
                <Row label="Unidad">{entity.display.unit}</Row>
                <Row label="URL de origen">
                  <span className="break-all font-mono text-[12px]">{entity.source_url || "—"}</span>
                </Row>
                <Row label="Descargado (UTC)">
                  <span className="font-mono">{entity.downloaded_at_utc || "—"}</span>
                </Row>
                <Row label="SHA-256">
                  <span className="font-mono break-all">{entity.sha256}</span>
                </Row>
                <Row label="Licencia">
                  {entity.license.id || "sin licencia verificada"} ·{" "}
                  {entity.license.attribution || "—"}
                </Row>
              </>
            )}
            <Row label="Perfil">
              <span className="font-mono">{entity.profile}</span>
            </Row>
            <Row label="Digest de validación">
              <span className="font-mono break-all">{data.digest}</span>
            </Row>
          </dl>
        </section>

        <section className="space-y-3">
          <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
            Gate humano
          </h2>
          <Card>
            <CardContent className="space-y-4 pt-4">
              {data.decision ? (
                <div className="space-y-1 border-b border-line pb-3">
                  <p className="text-[12px] uppercase tracking-wider text-muted">
                    Última decisión
                  </p>
                  <Badge
                    variant={
                      ["habilitado", "aprobar_con_excepcion"].includes(
                        data.decision.gate_decision,
                      )
                        ? "ok"
                        : "fail"
                    }
                  >
                    {data.decision.gate_decision}
                  </Badge>
                  <p className="text-[13px]">
                    <strong>{data.decision.operator}</strong> ·{" "}
                    <span className="font-mono">{data.decision.decided_at_utc}</span>
                  </p>
                  <p className="text-[13px]">{data.decision.rationale}</p>
                  <p className="break-all font-mono text-[11.5px] text-muted">
                    basis {data.decision.decision_basis_digest}
                  </p>
                </div>
              ) : null}

              <GateForm
                caseId={data.case_id}
                blocking={data.blocking}
                warnings={data.warnings}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Invalidación en vivo</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-3 text-[13px] text-muted">
                Enmienda la versión del perfil sin tocar el archivo. El digest cambia, la
                decisión se invalida y el agregado se retira del portal.
              </p>
              {data.override ? (
                <form action={undoSimulation.bind(null, data.case_id)}>
                  <Button type="submit" variant="secondary">
                    Retirar simulación
                  </Button>
                </form>
              ) : (
                <form action={simulate.bind(null, data.case_id)}>
                  <Button type="submit" variant="secondary">
                    Simular cambio en el perfil
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        </section>
      </div>

      <section className="space-y-3">
        <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
          Hallazgos por regla
        </h2>
        <p className="text-[12.5px] text-muted">
          SHA-256 del archivo evaluado:{" "}
          <span className="break-all font-mono">{data.entity.sha256}</span>
        </p>
        <Table>
          <THead>
            <TR>
              <TH>Regla</TH>
              <TH>Título</TH>
              <TH>Estado</TH>
              <TH>Crítica</TH>
              <TH>Mensaje</TH>
              <TH>Evidencia</TH>
            </TR>
          </THead>
          <TBody>
            {data.findings.map((finding) => (
              <TR key={finding.rule_id}>
                <TD className="whitespace-nowrap font-mono">{finding.rule_id}</TD>
                <TD>{finding.title}</TD>
                <TD className="whitespace-nowrap">
                  <SeverityBadge status={finding.status} />
                </TD>
                <TD className="whitespace-nowrap">{finding.critical ? "sí" : "no"}</TD>
                <TD>{finding.message}</TD>
                <TD className="max-w-[420px]">
                  <details>
                    <summary className="cursor-pointer text-[12.5px] text-muted">ver</summary>
                    <pre className="mt-1 whitespace-pre-wrap break-words font-mono text-[11px]">
                      {JSON.stringify(finding.evidence, null, 1)}
                    </pre>
                  </details>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </section>

      {data.comparisons.length ? (
        <section className="space-y-3">
          <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
            Comparaciones
          </h2>
          <Table>
            <THead>
              <TR>
                <TH>Solicitud</TH>
                <TH>Resultado</TH>
                <TH>Motivo</TH>
                <TH>Valor</TH>
                <TH>Evidencia privada</TH>
              </TR>
            </THead>
            <TBody>
              {data.comparisons.map((comparison) => {
                const evidence = (comparison.evidence ?? {}) as Record<string, unknown>;
                const privateEvidence = (comparison.private_evidence ?? {}) as Record<
                  string,
                  unknown
                >;
                const computed = privateEvidence.computed_pct;
                return (
                  <TR key={comparison.comparison_id}>
                    <TD>{comparison.label}</TD>
                    <TD className="whitespace-nowrap">
                      <Badge variant={comparison.status === "ok" ? "ok" : "fail"}>
                        {comparison.status}
                      </Badge>
                    </TD>
                    <TD>{comparison.reason}</TD>
                    <TD className="whitespace-nowrap">
                      {comparison.status === "ok" ? (
                        <>
                          {formatPct(evidence.published_pct as number)}
                          <div className="font-mono text-[11.5px] text-muted">
                            {String(evidence.published_cell ?? "")}
                          </div>
                        </>
                      ) : computed !== undefined ? (
                        <>
                          <strong>{formatPct(computed as number)}</strong>
                          <div className="text-[11.5px] text-muted">solo revisión</div>
                        </>
                      ) : (
                        "—"
                      )}
                    </TD>
                    <TD className="max-w-[360px]">
                      <pre className="whitespace-pre-wrap break-words font-mono text-[11px]">
                        {JSON.stringify(privateEvidence, null, 1)}
                      </pre>
                    </TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
          <p className="text-[12.5px] text-muted">
            El valor de una comparación bloqueada se ve aquí y no se copia al snapshot
            público, al export ni a la ficha de consulta.
          </p>
        </section>
      ) : null}

      <section className="space-y-3">
        <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
          Recibo
        </h2>
        <div className="flex items-center gap-3">
          <Link
            href={`/api/review-receipt/${data.case_id}`}
            className={buttonVariants({ variant: "secondary" })}
          >
            Descargar recibo.json
          </Link>
          <span className="text-[12.5px] text-muted">
            Separa <span className="font-mono">technical_payload</span> y{" "}
            <span className="font-mono">decision_log</span>. El digest no incluye
            timestamps.
          </span>
        </div>
      </section>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[200px_1fr] border-b border-line last:border-0">
      <dt className="bg-[#fafbfc] px-3 py-2 text-[13px] text-muted">{label}</dt>
      <dd className="min-w-0 px-3 py-2">{children}</dd>
    </div>
  );
}
