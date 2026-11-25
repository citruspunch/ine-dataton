import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, DownloadSimple } from "@phosphor-icons/react/dist/ssr";

import { SeverityBadge, StateBadge } from "@/components/badges";
import { DataList, DataRow } from "@/components/data-list";
import { PrintButton } from "@/components/print-button";
import { buttonVariants } from "@/components/ui/button";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { getJson } from "@/lib/api";
import type { AggregateDetail, Receipt } from "@/lib/types";
import { formatPct } from "@/lib/utils";

export const dynamic = "force-dynamic";

export const metadata = { title: "Ficha técnica" };

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
  const technical = receipt?.technical_payload as Record<string, unknown> | undefined;
  const rulesVersion = technical?.rules_version as string | undefined;

  return (
    <div className="space-y-6 print:space-y-4">
      <div className="flex flex-wrap items-center gap-2 print:hidden">
        <Link
          href={`/a/${aggregate.case_id}`}
          className={buttonVariants({ variant: "secondary", size: "sm" })}
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          Volver a la consulta
        </Link>
        <PrintButton />
        <Link
          href={`/api/receipt/${aggregate.case_id}`}
          className={buttonVariants({ variant: "secondary", size: "sm" })}
        >
          <DownloadSimple className="h-3.5 w-3.5" aria-hidden />
          recibo.json
        </Link>
      </div>

      <header className="flex flex-wrap items-start justify-between gap-4 border-b-2 border-brand pb-4">
        <div>
          <p className="text-[10.5px] font-bold uppercase tracking-[0.18em] text-brand">
            INE Data Trust · Ficha técnica de validación
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-ink">
            {entity.title || aggregate.label}
          </h1>
          <p className="mt-1 text-[12.5px] text-muted">
            Documento para adjuntar al ticket de publicación (procedimiento 18, pasos 4 a 6,
            como propuesta). No certifica el dato ni sustituye la revisión del productor.
          </p>
        </div>
        <div className="text-right text-[11.5px] text-muted">
          <Image
            src="/ine-logo.png"
            alt="Instituto Nacional de Estadística"
            width={7026}
            height={2273}
            className="ml-auto h-8 w-auto"
          />
          <p className="mt-2 font-mono">{aggregate.case_id}</p>
          <p className="font-mono">snapshot {String(technical?.snapshot_id ?? "—")}</p>
        </div>
      </header>

      <div className="flex flex-wrap items-center gap-2">
        <StateBadge state={aggregate.state} text={aggregate.state_text} />
        <span className="text-[12px] text-muted">
          Publicado el {aggregate.published_at_utc?.slice(0, 10)}
        </span>
      </div>

      <DataList>
        <DataRow label="Identificador">
          <span className="font-mono">{aggregate.case_id}</span>
        </DataRow>
        <DataRow label="Periodo">{entity.display.period}</DataRow>
        <DataRow label="Base">{entity.display.base}</DataRow>
        <DataRow label="Unidad">{entity.display.unit}</DataRow>
        <DataRow label="URL oficial">
          <span className="break-all font-mono text-[11.5px]">{entity.source_url || "—"}</span>
        </DataRow>
        <DataRow label="Descargado (UTC)">
          <span className="font-mono">{entity.downloaded_at_utc || "—"}</span>
        </DataRow>
        <DataRow label="SHA-256 del archivo">
          <span className="break-all font-mono text-[11.5px]">{entity.sha256}</span>
        </DataRow>
        <DataRow label="Licencia">
          {entity.license.id || "—"} · {entity.license.attribution || "—"}
        </DataRow>
        <DataRow label="Perfil declarativo">
          <span className="font-mono">{entity.profile}</span>
        </DataRow>
        <DataRow label="Versión de reglas">
          <span className="font-mono">{rulesVersion ?? "—"}</span>
        </DataRow>
        <DataRow label="Digest de validación">
          <span className="break-all font-mono text-[11.5px]">{aggregate.digest}</span>
        </DataRow>
      </DataList>

      <section className="space-y-2">
        <h2 className="text-[11.5px] font-bold uppercase tracking-[0.14em] text-brand">
          Resultado por regla
        </h2>
        <Table className="text-[12.5px] print:text-[10.5px]">
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
              <TR key={finding.rule_id} className="hover:bg-transparent">
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
          <h2 className="text-[11.5px] font-bold uppercase tracking-[0.14em] text-brand">
            Comparaciones evaluadas
          </h2>
          <Table className="text-[12.5px] print:text-[10.5px]">
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
                  <TR key={comparison.comparison_id} className="hover:bg-transparent">
                    <TD>{comparison.label}</TD>
                    <TD className="whitespace-nowrap">{comparison.status}</TD>
                    <TD>{comparison.reason}</TD>
                    <TD className="whitespace-nowrap">
                      {comparison.status === "ok" ? (
                        <>
                          {formatPct(evidence.published_pct as number)}{" "}
                          <span className="font-mono text-[11px] text-muted">
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
        <h2 className="text-[11.5px] font-bold uppercase tracking-[0.14em] text-brand">
          Decisión registrada
        </h2>
        {decision ? (
          <DataList>
            <DataRow label="Resultado del gate">{decision.gate_decision}</DataRow>
            <DataRow label="Responsable">{decision.operator}</DataRow>
            <DataRow label="Fecha (UTC)">
              <span className="font-mono">{decision.decided_at_utc}</span>
            </DataRow>
            <DataRow label="Motivo">{decision.rationale}</DataRow>
            <DataRow label="Digest de la decisión">
              <span className="break-all font-mono text-[11.5px]">
                {decision.decision_basis_digest}
              </span>
            </DataRow>
          </DataList>
        ) : (
          <p className="text-[13px] text-muted">Sin decisión registrada en el recibo público.</p>
        )}
      </section>

      <div className="grid gap-8 pt-6 sm:grid-cols-2">
        <div>
          <p className="mb-8 text-[12.5px] text-muted">Revisado por (publicaciones)</p>
          <div className="border-t border-[#8a97a8] pt-1 text-[11.5px] text-muted">
            Nombre y firma
          </div>
        </div>
        <div>
          <p className="mb-8 text-[12.5px] text-muted">Aprobado por (producción)</p>
          <div className="border-t border-[#8a97a8] pt-1 text-[11.5px] text-muted">
            Nombre y firma
          </div>
        </div>
      </div>

      <p className="border-t border-line pt-3 text-[11px] leading-relaxed text-muted">
        La habilitación corresponde a INE Data Trust, no al INE. Este documento no certifica.
        El digest no incluye timestamps de ejecución ni de decisión. Los datos conservan su
        licencia {entity.license.id || "original"}.
      </p>
    </div>
  );
}
