import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  ArrowUpRight,
  CalendarDots,
  DownloadSimple,
  FileText,
  Hash,
  ShieldCheck,
  Stack,
} from "@phosphor-icons/react/dist/ssr";

import { StateBadge } from "@/components/badges";
import { DataList, DataRow } from "@/components/data-list";
import { FindingsPanel } from "@/components/findings-panel";
import { PageHeader } from "@/components/page-header";
import { VariablesSummary } from "@/components/variables-summary";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getJson } from "@/lib/api";
import type { AggregateDetail, Receipt } from "@/lib/types";

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

  const facts = [
    { label: "Periodo", value: entity.display.period ?? "Sin dato", icon: CalendarDots },
    { label: "Base", value: entity.display.base ?? "Sin dato", icon: Hash },
    { label: "Unidad", value: entity.display.unit ?? "Sin dato", icon: Stack },
    {
      label: "Licencia",
      value: entity.license.id || "sin licencia",
      icon: ShieldCheck,
    },
  ];

  return (
    <div className="space-y-7">
      <VariablesSummary summary={entity.variables_summary} />
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-[14px] font-semibold text-brand hover:underline print:hidden"
      >
        <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
        Volver a la consulta
      </Link>

      <PageHeader
        title={entity.title || aggregate.label}
        description={
          <>
            El INE publicó este agregado y la validación lo habilitó para consulta el{" "}
            <span className="font-mono text-[13.5px]">
              {aggregate.published_at_utc?.slice(0, 10)}
            </span>
            . Esta validación no sustituye la revisión oficial.
          </>
        }
        actions={
          <>
            <Link
              href={`/a/${aggregate.case_id}/ficha`}
              className={buttonVariants({ variant: "secondary", size: "sm" })}
            >
              <FileText className="h-3.5 w-3.5" aria-hidden />
              Ficha imprimible
            </Link>
            <Link
              href={`/api/receipt/${aggregate.case_id}`}
              className={buttonVariants({ variant: "secondary", size: "sm" })}
            >
              <DownloadSimple className="h-3.5 w-3.5" aria-hidden />
              recibo.json
            </Link>
          </>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <StateBadge state={aggregate.state} text={aggregate.state_text} />
        {entity.topic === "ipc" ? <Badge variant="accent">IPC</Badge> : null}
        <Badge variant="none">no certifica</Badge>
        <span className="font-mono text-[12.5px] text-muted">{aggregate.case_id}</span>
      </div>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {facts.map((fact) => (
          <div
            key={fact.label}
            className="rounded-xl border border-line bg-white px-4 py-3 shadow-[0_1px_2px_rgba(16,32,52,.04)]"
          >
            <p className="flex items-center gap-1.5 text-[11.5px] font-bold text-muted">
              <fact.icon className="h-3.5 w-3.5 text-brand" aria-hidden />
              {fact.label}
            </p>
            <p className="mt-1.5 text-[15px] font-semibold leading-snug text-ink">
              {fact.value}
            </p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Reglas evaluadas</CardTitle>
            <p className="mt-1 text-[14px] text-muted">
              Resultado técnico de cada regla aplicada al archivo.
            </p>
          </CardHeader>
          <CardContent className="p-0">
            <FindingsPanel findings={aggregate.findings} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ficha técnica</CardTitle>
            <p className="mt-1 text-[14px] text-muted">
              Datos de procedencia y digest del archivo.
            </p>
          </CardHeader>
          <CardContent className="p-0">
            <DataList className="rounded-none border-0">
              <DataRow label="Fuente">
                {entity.title} · Instituto Nacional de Estadística
              </DataRow>
              <DataRow label="URL de origen">
                {entity.source_url ? (
                  <a
                    href={entity.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="break-all font-mono text-[12.5px] text-brand hover:underline"
                  >
                    {entity.source_url}
                    <ArrowUpRight className="ml-0.5 inline h-3 w-3" aria-hidden />
                  </a>
                ) : (
                  "Sin URL"
                )}
              </DataRow>
              <DataRow label="Descarga UTC">
                <span className="font-mono text-[13px]">
                  {entity.downloaded_at_utc || "Sin registro"}
                </span>
              </DataRow>
              <DataRow label="SHA-256">
                <span className="break-all font-mono text-[12.5px]">{entity.sha256}</span>
              </DataRow>
              <DataRow label="Licencia">
                {entity.license.id || "Sin licencia"} · {entity.license.attribution || "Sin atribución"}
              </DataRow>
              <DataRow label="Perfil">
                <span className="font-mono text-[13px]">{entity.profile}</span>
              </DataRow>
              <DataRow label="Digest">
                <span className="break-all font-mono text-[12.5px]">{aggregate.digest}</span>
              </DataRow>
            </DataList>
          </CardContent>
        </Card>
      </section>

      <p className="rounded-lg border border-line bg-brand-soft/60 px-4 py-3 text-[13px] leading-relaxed text-muted">
        {aggregate.notice}
      </p>
    </div>
  );
}
