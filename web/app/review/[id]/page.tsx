import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  ArrowUpRight,
  CheckCircle,
  DownloadSimple,
  FileMagnifyingGlass,
  Info,
  Scales,
  ShieldWarning,
} from "@phosphor-icons/react/dist/ssr";

import { StateBadge } from "@/components/badges";
import { DataList, DataRow } from "@/components/data-list";
import { FindingsPanel } from "@/components/findings-panel";
import { GateForm } from "@/components/gate-form";
import { PageHeader } from "@/components/page-header";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getJson } from "@/lib/api";
import type { ReviewPayload } from "@/lib/types";
import { formatPct } from "@/lib/utils";

export const dynamic = "force-dynamic";

export const metadata = { title: "Caso en revisión" };

interface PageProps {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ msg?: string; kind?: string }>;
}

const GATE_LABEL: Record<string, string> = {
  habilitado: "Habilitado",
  aprobar_con_excepcion: "Aprobado con excepción",
  rechazar: "Rechazado",
  revocado: "Revocado",
};

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
  const coverage = data.coverage;

  return (
    <div className="space-y-6">
      <Link
        href="/review"
        className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-brand hover:underline"
      >
        <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
        Volver a la bandeja
      </Link>

      <PageHeader
        eyebrow="Caso en revisión"
        title={data.label}
        description={
          <>
            <span className="font-mono text-[12.5px]">{data.case_id}</span> ·{" "}
            {data.method === "identity_pair"
              ? "contraste de identidad entre recursos"
              : "validación contra contrato declarativo"}
          </>
        }
        actions={
          <>
            {data.published ? (
              <Link
                href={`/a/${data.case_id}`}
                className={buttonVariants({ variant: "secondary", size: "sm" })}
              >
                <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
                Ver en consulta
              </Link>
            ) : null}
            <Link
              href={`/api/review-receipt/${data.case_id}`}
              className={buttonVariants({ variant: "secondary", size: "sm" })}
            >
              <DownloadSimple className="h-3.5 w-3.5" aria-hidden />
              recibo.json
            </Link>
          </>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <StateBadge state={data.state} text={data.state_text} />
        <Badge variant={data.published ? "ok" : "none"}>
          {data.published ? "publicado en consulta" : "no publicado"}
        </Badge>
        <Badge variant={coverage.complete ? "info" : "warn"}>
          {coverage.critical_evaluated}/{coverage.critical_total} críticas evaluadas
        </Badge>
        {data.override ? <Badge variant="warn">simulación de contrato activa</Badge> : null}
      </div>

      {query.msg ? (
        <Alert variant={query.kind === "err" ? "fail" : query.kind === "warn" ? "warn" : "ok"}>
          <CheckCircle className="h-4 w-4 shrink-0" aria-hidden />
          <span>{query.msg}</span>
        </Alert>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.65fr)_minmax(0,1fr)]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileMagnifyingGlass className="h-4 w-4 text-brand" aria-hidden />
                Ficha del recurso
              </CardTitle>
              <CardDescription>
                Identidad, procedencia y huella del archivo evaluado.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <DataList className="rounded-none border-0">
                {isPair ? (
                  <>
                    <DataRow label="Recursos">
                      <div className="space-y-1">
                        {(entity.resources ?? []).map((resource) => (
                          <div key={resource.manifest_item}>
                            <span className="font-mono text-[12px]">{resource.manifest_item}</span>
                            <span className="text-muted"> · {resource.identity.dataset}</span>
                          </div>
                        ))}
                      </div>
                    </DataRow>
                    <DataRow label="Mismos bytes">{entity.same_bytes ? "sí" : "no"}</DataRow>
                    <DataRow label="SHA-256">
                      <span className="break-all font-mono text-[12px]">{entity.sha256}</span>
                    </DataRow>
                  </>
                ) : (
                  <>
                    <DataRow label="Fuente">{entity.title}</DataRow>
                    <DataRow label="Origen">
                      {entity.origin === "upload"
                        ? "archivo cargado en la sesión"
                        : "recurso registrado en el snapshot"}
                    </DataRow>
                    <DataRow label="Periodo">{entity.display.period}</DataRow>
                    <DataRow label="Base">{entity.display.base}</DataRow>
                    <DataRow label="Unidad">{entity.display.unit}</DataRow>
                    <DataRow label="URL de origen">
                      {entity.source_url ? (
                        <a
                          href={entity.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="break-all font-mono text-[12px] text-brand hover:underline"
                        >
                          {entity.source_url}
                        </a>
                      ) : (
                        "—"
                      )}
                    </DataRow>
                    <DataRow label="Descargado (UTC)">
                      <span className="font-mono text-[12px]">
                        {entity.downloaded_at_utc || "—"}
                      </span>
                    </DataRow>
                    <DataRow label="SHA-256">
                      <span className="break-all font-mono text-[12px]">{entity.sha256}</span>
                    </DataRow>
                    <DataRow label="Licencia">
                      {entity.license.id || "sin licencia verificada"} ·{" "}
                      {entity.license.attribution || "—"}
                    </DataRow>
                  </>
                )}
                <DataRow label="Perfil">
                  <span className="font-mono text-[12px]">{entity.profile}</span>
                </DataRow>
                <DataRow label="Digest de validación">
                  <span className="break-all font-mono text-[12px]">{data.digest}</span>
                </DataRow>
              </DataList>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Scales className="h-4 w-4 text-brand" aria-hidden />
                Hallazgos por regla
              </CardTitle>
              <CardDescription>
                {data.findings.length} reglas evaluadas. Abra una fila para ver su evidencia.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <FindingsPanel findings={data.findings} />
            </CardContent>
          </Card>

          {data.comparisons.length ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShieldWarning className="h-4 w-4 text-brand" aria-hidden />
                  Comparaciones
                </CardTitle>
                <CardDescription>
                  Valores calculados solo para revisión. Los bloqueados nunca se copian al
                  snapshot público.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.comparisons.map((comparison) => {
                  const evidence = (comparison.evidence ?? {}) as Record<string, unknown>;
                  const privateEvidence = (comparison.private_evidence ?? {}) as Record<
                    string,
                    unknown
                  >;
                  const computed = privateEvidence.computed_pct;
                  return (
                    <div
                      key={comparison.comparison_id}
                      className="rounded-lg border border-line bg-[#fafafa] p-4"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <p className="text-[13.5px] font-semibold text-ink">
                            {comparison.label}
                          </p>
                          <p className="mt-0.5 font-mono text-[11px] text-muted">
                            {comparison.comparison_id}
                          </p>
                        </div>
                        <Badge variant={comparison.status === "ok" ? "ok" : "warn"}>
                          {comparison.status === "ok" ? "verificada" : "bloqueada"}
                        </Badge>
                      </div>
                      <p className="mt-2 text-[12.5px] leading-relaxed text-muted">
                        {comparison.reason}
                      </p>
                      <div className="mt-3 grid gap-3 sm:grid-cols-2">
                        <div className="rounded-md border border-line bg-white px-3 py-2">
                          <p className="text-[10.5px] font-bold uppercase tracking-[0.1em] text-muted">
                            {comparison.status === "ok" ? "Variación publicada" : "Cálculo de revisión"}
                          </p>
                          <p className="mt-0.5 text-[15px] font-semibold text-ink">
                            {comparison.status === "ok"
                              ? formatPct(evidence.published_pct as number)
                              : computed !== undefined
                                ? formatPct(computed as number)
                                : "—"}
                          </p>
                          {comparison.status === "ok" && evidence.published_cell ? (
                            <p className="font-mono text-[11px] text-muted">
                              celda {String(evidence.published_cell)}
                            </p>
                          ) : comparison.status !== "ok" ? (
                            <p className="text-[11px] text-warn">solo revisión</p>
                          ) : null}
                        </div>
                        <details className="rounded-md border border-line bg-white px-3 py-2">
                          <summary className="cursor-pointer text-[12px] font-semibold text-brand">
                            Evidencia
                          </summary>
                          <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-words font-mono text-[11px] leading-relaxed">
                            {JSON.stringify(
                              Object.keys(privateEvidence).length ? privateEvidence : evidence,
                              null,
                              2,
                            )}
                          </pre>
                        </details>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          ) : null}
        </div>

        <aside className="space-y-5 lg:sticky lg:top-24 lg:self-start">
          {data.decision ? (
            <Card>
              <CardHeader>
                <CardTitle>Última decisión</CardTitle>
                <CardDescription>
                  Registro que sostiene el estado actual del agregado.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2.5 text-[13px]">
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      ["habilitado", "aprobar_con_excepcion"].includes(
                        data.decision.gate_decision,
                      )
                        ? "ok"
                        : "fail"
                    }
                  >
                    {GATE_LABEL[data.decision.gate_decision] ?? data.decision.gate_decision}
                  </Badge>
                  <span className="text-[12px] text-muted">
                    {data.decision.decided_at_utc}
                  </span>
                </div>
                <p>
                  <span className="font-semibold">{data.decision.operator}</span>
                </p>
                <p className="leading-relaxed text-muted">{data.decision.rationale}</p>
                <p className="break-all font-mono text-[11px] text-muted/80">
                  basis {data.decision.decision_basis_digest}
                </p>
              </CardContent>
            </Card>
          ) : null}

          <Card>
            <CardHeader>
              <CardTitle>Gate humano</CardTitle>
              <CardDescription>
                {data.decision
                  ? "Puede registrar una nueva decisión; la anterior queda en el historial."
                  : "La habilitación exige una decisión explícita y trazable."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <GateForm
                caseId={data.case_id}
                blocking={data.blocking}
                warnings={data.warnings}
              />
            </CardContent>
          </Card>

          <div className="flex gap-2.5 rounded-lg border border-line bg-white px-4 py-3 text-[12px] leading-relaxed text-muted">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-brand" aria-hidden />
            <p>
              Habilitar no certifica el dato: registra que el archivo coincidió con su
              contrato, que la licencia está verificada y que una persona asumió la decisión.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
